"""The revamp art style, the shape-matched ASCII renderer behind its
scenery, and ` for the next theme."""
import os, re, sys, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.config import ART_STYLES
from minitype.settings import Settings
from minitype.terminal import console, keys, style
from minitype.terminal.art import ART, LARGE, THEME_ART, revamp
from minitype.context import App
from minitype.ui import main_menu as mm, settings_menu as sm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)

# ---------------------------------------------------------------- the style
assert ART_STYLES[0] == "revamp" and Settings().art_style == "revamp"
allowed = set(chr(c) for c in range(32, 127)) | set("¯·°")
for t in style.theme_names():
    if t == "mono":
        continue
    name = THEME_ART[t]
    pieces = style.theme_art(t, "revamp")
    sizes = revamp(name)
    big = sizes[0]
    assert pieces[:len(sizes)] == sizes and         [list(p.lines) for p in pieces[len(sizes):]] == [LARGE[name][0], ART[name]], t
    if big.back_parts:
        assert [len(p.lines) for p in sizes] == [28, 22, 16], (name, "three sizes, biggest first")
    else:
        assert len(sizes) == 1, (t, "one size")
    assert len({len(l) for l in big.lines}) == 1, name
    if big.back_parts:
        # the big ones, every technique at once (tools/art_wow.py)
        assert len(big.lines) == 28, (name, len(big.lines))
        assert set("".join(big.back_parts)) <= set("dtexagw "), name
    else:
        assert 8 <= len(big.lines) <= 16, (name, len(big.lines))
        chars = set("".join(big.lines))
        assert chars <= allowed, (name, chars - allowed)
    assert set("".join(big.parts)) <= set("dtexagw "), name
    assert all((ch == " ") == (p == " ") for l, q in zip(big.lines, big.parts) for ch, p in zip(l, q)), name
    assert any(k < len(big.lines[0]) for k in big.keep), (name, "has a subject")
    # the subject is on the right; scenery may run left of it
    assert max(len(l.rstrip()) for l in big.lines) > len(big.lines[0]) - 8, name
spanning = [n for n in set(THEME_ART.values()) if revamp(n)[0].span]
big = [n for n in set(THEME_ART.values()) if revamp(n)[0].back_parts]
assert {"island", "moon", "pines", "fire", "keyboard"} <= set(big), big
# they step aside: only their subject is focus, the sky and ground are backdrop
for n in big:
    p = revamp(n)[0]
    assert sum(k < len(p.lines[0]) for k in p.keep) < len(p.lines), (n, "not all focus")
assert len(spanning) >= 20, spanning

# it draws, coloured, in the app
app = App(); app.settings.theme = "midnight"; app.styles()
assert console._decor["art"][0].lines == revamp("moon")[0].lines

# ---------------------------------------------------------------- the renderer
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools")]
import artgen, artgen_ascii
from artgen import Line


def one_line(points, rows=4, cols=12):
    sc = artgen.Scene(cols / (2 * rows), [Line([(x / (2 * rows), y / rows) for x, y in points], "a")])
    return ["".join(r) for r in artgen_ascii.render(sc, rows, raw=True)[0]]


# a flat line lands at its height in the cell: bottom _, middle -, top ¯
assert set(one_line([(0, 1.92), (12, 1.92)])[1].strip()) == {"_"}
assert set(one_line([(0, 1.5), (12, 1.5)])[1].strip()) == {"-"}
assert set(one_line([(0, 1.06), (12, 1.06)])[1].strip()) <= {"¯", "'", "`"}
# upright and diagonal lines take | / \, one character a row, no gaps
up = one_line([(6.5, 0), (6.5, 4)])
assert all(r.strip() == "|" for r in up), up
down = one_line([(2, 0), (6, 4)], rows=4, cols=12)
assert all(r.strip() in ("\\",) for r in down), down
rise = one_line([(2, 4), (6, 0)], rows=4, cols=12)
assert all(r.strip() == "/" for r in rise), rise

# ---------------------------------------------------------------- ` changes theme
console.term_size = lambda: (100, 30)
a = App()
seq = iter(["`", "`", keys.ESC, keys.ESC, keys.ESC])
frames = []
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
        mock.patch.object(console, "present", lambda lines, focus=None, pinned=(), **k: frames.append(lines)):
    mm.main_menu(a)
names = style.theme_names()
assert a.settings.theme == names[2], a.settings.theme
assert any("theme  ocean" in strip(l) for l in frames[1]), "says which"
# typing in the settings search takes it as text
b = App()
seq = iter(["`", keys.CTRL_C])
with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
        mock.patch.object(console, "present", lambda *x, **k: None):
    sm.settings_menu(b)
assert b.settings.theme == "default"
# it wraps round, through your own themes too
a.settings.theme = names[-1]
from minitype.ui.screen import next_theme
next_theme(a)
assert a.settings.theme == names[0]
print("ALL OK")
