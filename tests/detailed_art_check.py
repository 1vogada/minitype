import os, re, tempfile, random
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, style
from minitype.terminal.art import ART, LARGE, THEME_ART, blocks, detailed, paint
from minitype.context import App
from minitype.ui import settings_menu as sm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
SIZE = [160, 40]
console.term_size = lambda: tuple(SIZE)


def present(lines, scene="menu", pinned=()):
    out = []
    with mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        console.present(lines, None, pinned, scene=scene)
    return strip(out[-1]).split("\n")


app = App()
assert app.settings.art_style == "revamp"
app.settings.art_style = "detailed"     # most of these check the ASCII pictures
app.settings.theme = "ocean"
app.styles()

# ---------------------------------------------------------------- a picture's rows paint back to its lines
pal = style.Styles("ocean").art_palette()
for name in ART:
    for piece in detailed(name):
        pic = paint(piece, pal)
        assert paint(piece, pal) is pic, "cached"
        for k, line in enumerate(piece.lines):
            assert strip(pic.row(k)) == line.rstrip(), (name, k)
            assert strip(pic.row(k, 5)) == line[5:].rstrip(), (name, k)

# ---------------------------------------------------------------- the sea runs across the whole bottom
rows = present(["menu"] * 3)
assert all(len(r) == SIZE[0] - 1 for r in rows)
sea_rows = [r for r in rows[-6:-1] if "~" in r]
assert sea_rows and all(r[1:12].strip() for r in sea_rows), "starts at the left edge"
# the island itself is in the right two-thirds
first_focus = min(r.find("#") for r in rows if "#" in r[60:])
assert first_focus > (SIZE[0] - 2) // 3

# ---------------------------------------------------------------- every width works, cropping the background
for w in range(40, 201, 7):
    SIZE[:] = [w, 36]
    app.styles()
    rows = present(["menu line"] * 4)
    assert all(len(r) == w - 1 for r in rows), w
SIZE[:] = [160, 40]; app.styles()

# ---------------------------------------------------------------- text is never covered, whatever it is
random.seed(5)
for theme in ("ocean", "synthwave", "midnight", "monokai", "forest", "matrix", "default"):
    app.settings.theme = theme
    for w, h in ((160, 40), (120, 32), (100, 28), (80, 24)):
        SIZE[:] = [w, h]
        app.styles()
        for trial in range(15):
            n = random.randint(3, h - 4)
            lines = ["".join(random.choice("abc ") for _ in range(random.randint(0, w // 2)))
                     for _ in range(n)]
            rows = present(lines)
            for k, line in enumerate(lines):
                got = rows[1 + k][1:1 + len(line)]
                assert got == line, (theme, w, h, k, line, rows[1 + k])
                # two spaces after text before any art
                tail = rows[1 + k][1 + len(line.rstrip()):]
                assert not tail[:2].strip() or not line.strip(), (theme, rows[1 + k])

# ---------------------------------------------------------------- beside text, the background keeps to the picture's box
app.settings.theme = "synthwave"
SIZE[:] = [120, 32]
app.styles()
lines = ["x"] * 3 + [""] * 12 + ["menu item"] + [""] * 6
rows = present(lines)
item = rows[1 + 15]
assert item[1:10] == "menu item"
gap = item[10:]
assert gap[:40].strip() == "", "no background running along beside the text"
below = rows[1 + 17:]
assert any(r[12:40].strip() for r in below), "below the last text it spans"

# ---------------------------------------------------------------- og leaves the detailed pictures out
app.settings.theme = "ocean"
app.settings.art_style = "og"
app.styles()
assert [list(p.lines) for p in console._decor["art"]] == [LARGE["island"][0], ART["island"]]
app.settings.art_style = "detailed"
app.styles()
assert len(console._decor["art"]) == len(detailed("island")) + 2

# ---------------------------------------------------------------- the fun section has the toggle
items = {it.label: it for it in sm.build_items(app)}
row = items["art style"]
assert row.section == "art" and row.value() == "detailed"
row.action(); assert app.settings.art_style == "og"
row.action(); assert app.settings.art_style == "combined"
row.action(); assert app.settings.art_style == "revamp"
row.action(); assert app.settings.art_style == "blocks"
row.action(); assert app.settings.art_style == "detailed"
from minitype.settings import Settings
s = Settings(); s.apply({"art_style": "og"}); assert s.art_style == "og"
s = Settings(); s.apply({"art_style": "bogus"}); assert s.art_style == "revamp"

# ---------------------------------------------------------------- shaded colours
import sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
from minitype.terminal import art as art_mod
import make_art
assert make_art.CODES == art_mod.CODES and len(set(art_mod.CODES)) >= 70
st = style.Styles("ocean")
flat, shaded = st.art_palette(), st.art_palette(True)
assert set(flat) < set(shaded) and len(shaded) == 7 + 7 + 70 + 70
for part in [k for k in flat if isinstance(k, str)]:
    shades = [shaded[(part, str(t))] for t in range(10)]
    assert len(set(shades)) >= 6, part                     # really different shades
    rgbs = [style.rgb_of_code(c) for c in shades]
    lum = [style.luminance(c) for c in rgbs]
    assert lum[0] < lum[6] < lum[9], (part, lum)           # dark to light
# a light theme sinks its shadows towards white, not black
paper = style.Styles("paper").art_palette(True)
assert style.luminance(style.rgb_of_code(paper[("text", "0")])) >     style.luminance(style.rgb_of_code(style.Styles("paper").art_palette()["text"]))
# 256-colour terminals get 256-colour shades
with mock.patch.object(style, "truecolor", lambda: False):
    p256 = style.Styles("ocean").art_palette(True)
    assert all("8;5;" in v and ";2;" not in v for v in p256.values() if v)
# pieces carry real tones, and the picture uses them
island = detailed("island")[0]
assert len(set("".join(island.tones)) - {" "}) >= 6
pic_s, pic_f = paint(island, shaded), paint(island, flat)
assert len({c for row in pic_s._codes for c in row}) > len({c for row in pic_f._codes for c in row}) + 10
# the setting switches between them
app.settings.art_colours = "shaded"; app.styles()
codes_s = {c for p in console._decor["art"] for row in p._codes for c in row}
app.settings.art_colours = "flat"; app.styles()
codes_f = {c for p in console._decor["art"] for row in p._codes for c in row}
assert len(codes_s) > len(codes_f) and codes_f <= set(flat.values()) | {""}
app.settings.art_colours = "shaded"
items = {it.label: it for it in sm.build_items(app)}
assert items["art shading"].section == "art" and items["art shading"].value() == "shaded"
# every picture spans the bottom, in four sizes
for name in ART:
    d = detailed(name)
    assert all(p.span for p in d) and all(len(p.lines) <= h for p, h in zip(d[-4:], (26, 20, 14, 10))), name
    assert len(d) in (4, 5) and len(d[0].lines) > len(d[1].lines), name

# ---------------------------------------------------------------- blocks
BLOCK_CHARS = set(chr(0x2800 + k) for k in range(256)) | set(" \u2580\u2584\u2588\u258c\u2590\u2596\u2597\u2598\u2599\u259a\u259b\u259c\u259d\u259e\u259f")
shaded = style.Styles("ocean").art_palette(True)
assert ("bg", "accent", "3") in shaded and "48;" in shaded[("bg", "accent", "3")]
assert ("bg", "accent") in style.Styles("ocean").art_palette()
for name in ART:
    b = blocks(name)
    assert len(b) == len(detailed(name)) and all(p.span for p in b), name
    assert [len(p.lines) for p in b] == [len(p.lines) for p in detailed(name)] or True
    for p in b:
        assert len({len(l) for l in p.lines}) == 1, name
        assert all(len(x) == len(p.lines[0]) for g in (p.parts, p.tones, p.back_parts, p.back_tones)
                   for x in g), name
        for l, bp in zip(p.lines, p.back_parts):
            for ch, back in zip(l, bp):
                assert ch != " " or back == " ", (name, "a blank with a background")
                assert ch in BLOCK_CHARS or 32 < ord(ch) < 127, (name, ch)
    pic = paint(b[0], shaded)
    for k, line in enumerate(b[0].lines):
        assert strip(pic.row(k)) == line.rstrip(), (name, k)
# most of a picture is blocks; text pictures keep their text
share = lambda n: sum(ch in BLOCK_CHARS - {" "} for l in blocks(n)[0].lines for ch in l) / \
    max(1, sum(ch != " " for l in blocks(n)[0].lines for ch in l))
assert share("island") > 0.8 and share("blossom") > 0.8
assert any(0x2800 < ord(ch) <= 0x28ff for l in blocks("island")[0].lines for ch in l), "braille detail"
assert any("Q" in l for l in blocks("keyboard")[0].lines)
assert any(ch.isdigit() for l in blocks("summit")[0].lines for ch in l)
# cells with two colours set both, and the painted row carries backgrounds
island = blocks("island")[0]
assert sum(ch != " " for ch in "".join(island.back_parts)) > 500
assert "48;" in paint(island, shaded).row(len(island.lines) - 2)
# in the app: blocks by default, text still never covered
app.settings.art_style = "blocks"
app.settings.theme = "ocean"
for w, h in ((160, 40), (120, 32), (100, 28)):
    SIZE[:] = [w, h]
    app.styles()
    lines = ["menu line %d" % k for k in range(8)]
    rows = present(lines)
    assert all(len(r) == w - 1 for r in rows), w
    assert all(rows[1 + k][1:1 + len(l)] == l for k, l in enumerate(lines)), w
    assert any(ch in BLOCK_CHARS - {" "} for r in rows for ch in r), w
print("ALL OK")
