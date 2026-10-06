import json, os, re, tempfile, time
HOME = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = HOME
from unittest import mock
from minitype.terminal import console, keys, style
from minitype.terminal.art import ART, LARGE, THEME_ART, Piece, blocks, detailed
from minitype.terminal import art as art_mod
from minitype.context import App
from minitype.ui import main_menu as mm, settings_menu as sm, theme_creator as tc

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
SIZE = [100, 30]
console.term_size = lambda: tuple(SIZE)


def screen(app, fn=mm.main_menu):
    out = []
    seq = iter([keys.ESC, keys.ESC])
    with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        fn(app)
    frame = [o for o in out if o.startswith("\x1b[H")][0]
    return strip(frame).split("\n"), frame


def present(lines, scene="menu", pinned=()):
    out = []
    with mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        console.present(lines, None, pinned, scene=scene)
    return strip(out[-1]).split("\n")


# ---------------------------------------------------------------- art is all ASCII and every theme has some
for name, lines in ART.items():
    assert all(32 <= ord(c) < 127 for l in lines for c in l), name
    assert len(lines) <= 10 and max(map(len, lines)) <= 30, name
for name, (lines, colours) in LARGE.items():
    assert all(32 <= ord(c) < 127 for l in lines for c in l), name
    assert len(lines) <= 14 and max(map(len, lines)) <= 48, name
    assert len(lines) > len(ART[name]) or max(map(len, lines)) > max(map(len, ART[name])), name
assert set(LARGE) == set(ART)
# og: the large picture with the small one to fall back on; detailed: its
# detailed sizes, biggest first, before those
for t in style.theme_names():
    if t != "mono":
        name = THEME_ART[t]
        og = [list(p.lines) for p in style.theme_art(t, "og")]
        assert og == [LARGE[name][0], ART[name]], t
        d = style.theme_art(t)
        assert len(d) == len(blocks(name)) + 2 and d[-2:] == style.theme_art(t, "og"), t
        assert d[:-2] == blocks(name) and style.theme_art(t, "detailed")[:-2] == detailed(name), t
        heights = [len(p.lines) for p in detailed(name)]
        assert heights == sorted(heights, reverse=True) and heights[0] > len(LARGE[name][0]), t
assert style.theme_art("mono") == [] and style.theme_art("mono", "og") == []
for name in ART:
    for p in detailed(name):
        assert all(32 <= ord(c) < 127 for l in p.lines for c in l), name
        assert len({len(l) for l in p.lines}) == 1 and len(p.parts) == len(p.lines), name
        assert all(len(a) == len(b) for a, b in zip(p.lines, p.parts)), name
        assert all((ch == " ") == (c == " ") for l, q in zip(p.lines, p.parts)
                   for ch, c in zip(l, q)), name
        assert set("".join(p.parts)) <= set("dtexagw "), name
        assert len(p.keep) == len(p.lines) and any(k < len(p.lines[0]) for k in p.keep), name

# ---------------------------------------------------------------- borders
app = App()
assert app.settings.border == "rounded" and app.settings.art == "menus"
for border, corners in (("ascii", "++++"), ("line", "┌┐└┘"),
                        ("rounded", "╭╮╰╯"),
                        ("double", "╔╗╚╝"),
                        ("heavy", "┏┓┗┛")):
    app.settings.border = border
    rows, raw = screen(app)
    assert len(rows) == SIZE[1], (border, len(rows))
    assert rows[0][0] == corners[0] and rows[0][-1] == corners[1], border
    assert rows[-1][0] == corners[2] and rows[-1][-1] == corners[3], border
    assert all(len(r) == SIZE[0] - 1 for r in rows), "one column short of the edge"
    assert style.Styles("default").title + corners[0] in raw, "border in the accent colour"
# block: one column of full blocks; thick: two-column sides
for border, side in (("block", 1), ("thick", 2)):
    app.settings.border = border
    rows, raw = screen(app)
    assert len(rows) == SIZE[1] and all(len(r) == SIZE[0] - 1 for r in rows), border
    assert set(rows[0]) == {"█"} and set(rows[-1]) == {"█"}, border
    assert all(r[:side] == r[-side:] == "█" * side and r[side] != "█" for r in rows[1:-1]), border
    app.styles()
    assert console.size() == (SIZE[0] - 2 * side, SIZE[1] - 2), border
app.settings.border = "off"
rows, _ = screen(app)
assert rows[1].strip() == "minitype" or rows[2].strip() == "minitype"
assert "╭" not in "".join(rows)
# screens lay out inside the border
app.settings.border = "rounded"
app.styles()
assert console.size() == (SIZE[0] - 2, SIZE[1] - 2)
app.settings.border = "off"; app.styles()
assert console.size() == tuple(SIZE)

# ---------------------------------------------------------------- art
app = App()
assert app.settings.art_style == "revamp"
app.settings.art_style = "og"        # these check the original pictures
app.settings.art_colours = "flat"    # in the theme's own colours
app.settings.theme = "ocean"
app.settings.hints = False           # nothing pinned at the bottom
rows, raw = screen(app)
island = LARGE["island"][0]
text = "\n".join(rows)
assert all(line.strip() in text for line in island), "the large island is on screen"
st_ = style.Styles("ocean")
assert st_.title in raw and st_.good in raw, "painted in several of the theme's colours"
# a smaller terminal falls back to the small island
SIZE[:] = [50, 18]; app.styles()
text = "\n".join(present(["x"] * 3))
assert all(l.strip() in text for l in ART["island"]) and "(     )" not in text
SIZE[:] = [100, 30]; app.styles()
# it's at the bottom right, inside the border
last_art = max(i for i, r in enumerate(rows) if "~~~~" in r)
assert last_art == len(rows) - 2 and rows[last_art].rstrip("│ ").endswith("~")
# it never covers text: a long line in its corner keeps it off
SIZE[:] = [100, 30]
app.styles()
lines = ["x"] * 28
lines[25] = "y" * 90
assert not any("~~~~" in r for r in present(lines))
assert any("~~~~" in r for r in present(["x"] * 3))
# too small: left out
SIZE[:] = [40, 10]; app.styles()
assert not any("~~~~" in r for r in present(["x"] * 3))
SIZE[:] = [100, 30]; app.styles()
# scope: menus only by default; everywhere; off
assert not any("~~~~" in r for r in present(["x"] * 3, scene="test"))
app.settings.art = "everywhere"; app.styles()
assert any("~~~~" in r for r in present(["x"] * 3, scene="test"))
app.settings.art = "off"; app.styles()
assert not any("~~~~" in r for r in present(["x"] * 3))
app.settings.art = "menus"
# disguised hides border and art
app.settings.lowkey = "disguised"; app.styles()
r = present(["x"] * 3)
assert not any("~~~~" in x or "╭" in x for x in r)
app.settings.lowkey = "off"
# pinned hint lines: the art sits above them
app.styles()
r = present(["x"] * 3, pinned=["", "hint line"])
assert "hint line" in r[-2] and any("~~~~" in x for x in r[:-3])

# ---------------------------------------------------------------- the typing screen fits inside the border
from minitype.engine.runner import TypingTest
from minitype.engine.render import draw
from minitype.engine.spec import TestSpec
app = App()
words = tuple(("alpha beta gamma delta " * 20).split())
t = TypingTest(app, TestSpec("c", "words", len(words), "custom", words))
out = []
with mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    st = app.styles()
    draw(st, app.settings, "head", t.words, t.typed, t.wi, console.size()[0] - 4, "foot")
rows = strip(out[-1]).split("\n")
assert all(len(r) == SIZE[0] - 1 for r in rows) and rows[0][0] == "╭"
assert not any("~~~~" in r for r in rows), "no art on the typing screen by default"

# ---------------------------------------------------------------- your own themes
path = os.path.join(HOME, "themes.json")
json.dump({
    "named": {"base": "nord", "art": "cat"},
    "own": {"base": "nord", "art": ["  /\\", " /  \\", "/____\\"]},
    "bare": {"base": "nord", "art": "none"},
    "inherits": {"base": "ocean"},
    "child": {"base": "default", "art": "moon"},
}, open(path, "w", encoding="utf-8"))
assert [list(x.lines) for x in style.theme_art("named", "og")] == [LARGE["cat"][0], ART["cat"]]
assert style.theme_art("named")[0] == blocks("cat")[0]
assert [p.lines for p in style.theme_art("own")] == [("  /\\", " /  \\", "/____\\")]
assert style.theme_art("bare") == []
assert list(style.theme_art("inherits")[-1].lines) == ART["island"]
assert style.custom_error() == ""
time.sleep(0.02)
json.dump({"bad": {"base": "nord", "art": "unicorn"},
           "huge": {"base": "nord", "art": ["x" * 60]},
           "ok": {"base": "nord"}}, open(path, "w", encoding="utf-8"))
os.utime(path, (time.time() + 3, time.time() + 3))
err = style.custom_error()
assert "bad: art should be" in err and "huge: art can be at most" in err, err
os.remove(path)

# ---------------------------------------------------------------- settings rows and the creator
rows_ = {it.label: it for it in sm.build_items(App())}
assert rows_["border"].section == "interface" and rows_["show art"].section == "art"
assert rows_["border"].value() == "rounded" and rows_["show art"].value() == "menus"
app = App()
d = tc.Draft.from_theme("ocean")
items = {it.label: it for it in tc.build_items(app, d)}
assert items["art"].value() == "from base"
items["art"].action(); assert d.spec["art"] == "none"
items["art"].action(); assert d.spec["art"] == "keyboard"
items["art"].back(); items["art"].back(); assert "art" not in d.spec
items["art"].back(); assert d.spec["art"] == "summit", "wraps to the last picture"
# the creator shows the draft's picture while you're in it
_, focus = tc.draw(app, d, tc.Menu(tc.build_items(app, d), {}, "c"))
from minitype.terminal.art import revamp
assert [list(p.lines) for p in console._decor["art"]] ==     [list(p.lines) for p in revamp("summit")] + [LARGE["summit"][0], ART["summit"]]
app.settings.art_style = "og"
tc.draw(app, d, tc.Menu(tc.build_items(app, d), {}, "c"))
assert [list(p.lines) for p in console._decor["art"]] == [LARGE["summit"][0], ART["summit"]]
print("ALL OK")
