"""Art fading into the screen (dithered edges, corner) and its settings."""
import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
from unittest import mock
from minitype.config import ART_FADES
from minitype.settings import Settings
from minitype.terminal import console, keys, style
from minitype.terminal.art import paint, revamp
from minitype.context import App
from minitype.ui import settings_menu as sm
from minitype.ui.gallery import gallery

pal = style.Styles("forest").art_palette(True)
pic = paint(revamp("pines")[0], pal)
assert pic.back
same = pic.faded("off")
assert same is pic
e = pic.faded("edges", 100, 12, 70)
assert e is pic.faded("edges", 100, 12, 70), "kept, not redone every frame"
assert (e.height, e.width) == (pic.height, pic.width)
inked = lambda p, r: sum(ch != " " for ch in p.lines[r])
# the top rows thin out (some cells go, some turn to shades); the rest is untouched
assert inked(e, 0) < inked(pic, 0)
assert any(ch in "░▒▓" for ch in e.lines[1] + e.lines[2])
assert e.lines[-1][20:] == pic.lines[-1][20:] and e._codes[-1][20:] == pic._codes[-1][20:]
# the left side thins out too
assert sum(e.lines[r][0] != " " for r in range(e.height)) < sum(pic.lines[r][0] != " " for r in range(pic.height))
# a shade takes the colour it replaced, as its ink, with no background
for r in range(e.height):
    for c, ch in enumerate(e.lines[r]):
        if ch in "░▒▓" and pic.lines[r][c] != ch:
            assert "\x1b[48;" not in e._codes[r][c] and "38;" in e._codes[r][c]
# corner: the bottom right corner stays, the far corner goes
k = pic.faded("corner", 100, 12, 60)
assert k.lines[-1][-10:] == pic.lines[-1][-10:]
assert inked(k, 0) < inked(pic, 0) / 2
# bigger round keeps more
assert sum(inked(pic.faded("corner", 100, 12, 100), r) for r in range(pic.height)) > \
    sum(inked(k, r) for r in range(pic.height))
# on a screen wider than the picture it grows - and the grown one fades too
# (it lost the "has backgrounds" flag once, so wide windows got no fade)
wide = pic.wider(pic.width + 80)
assert wide is not pic and wide.back
assert wide.faded("edges", 100, 12, 70) is not wide
app0 = App(); app0.settings.theme = "ocean"; app0.styles()
console.term_size = lambda: (240, 60)
out = []
with mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    console.present(["  x"] * 3, None)
assert sum(out[-1].count(c) for c in "░▒▓") > sum(ch in "░▒▓" for l in revamp("island")[0].lines for ch in l),     "a 240-wide window fades the art"
# pictures without backgrounds (ASCII) are left alone when drawn
app = App(); app.settings.theme = "forest"; app.settings.art_style = "detailed"; app.styles()
console.term_size = lambda: (150, 42)
d = console._decor["art"][0]
assert not d.back

# ---------------------------------------------------------------- settings
s = Settings()
assert (s.art_fade, s.fade_top, s.fade_side, s.fade_round) == ("edges", 100, 12, 70)
assert ART_FADES[0] == "edges"
s.apply({"art_fade": "corner", "fade_top": 50, "fade_side": 24, "fade_round": 50})
assert (s.art_fade, s.fade_top, s.fade_side, s.fade_round) == ("corner", 50, 24, 50)
s = Settings(); s.apply({"art_fade": "x", "fade_top": 7, "fade_round": 5})
assert (s.art_fade, s.fade_top, s.fade_round) == ("edges", 100, 70), "old row counts fall back"
rows = {it.label: it for it in sm.build_items(App())}
for label in ("art fade", "fade top", "fade side", "fade round"):
    assert rows[label].section == "art", label
assert rows["fade top"].value() == "100%" and rows["fade round"].value() == "70%"
a = App(); a.styles()
assert console._decor["fade"] == ("edges", 100, 12, 70)
# d in the gallery steps it; esc puts it back, enter keeps
g = App()
seq = iter(["d", keys.ENTER])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)), \
        mock.patch.object(console, "present", lambda *x, **kw: None):
    gallery(g)
assert g.settings.art_fade == ART_FADES[1]
seq = iter(["d", keys.ESC])
with mock.patch.object(keys, "read_key", lambda *x, **kw: next(seq)), \
        mock.patch.object(console, "present", lambda *x, **kw: None):
    gallery(g)
assert g.settings.art_fade == ART_FADES[1]
# the curve: almost nothing at the very top, more and more art lower down,
# lightly dithered most of the way (an exponential)
from minitype.terminal.art import _curve
assert _curve(0) == 0 and abs(_curve(1) - 1) < 1e-9
assert _curve(0.5) > 0.7 and _curve(0.1) < 0.3
left = [sum(ch not in " ░▒▓" for ch in e.lines[r]) / max(1, sum(ch != " " for ch in pic.lines[r]))
        for r in range(e.height)]
assert left[0] < 0.05 and left[-2] > left[e.height // 2] > left[2], left
# half way: the top half fades, the bottom half is left alone
half = pic.faded("edges", 50, 0, 70)
assert half.lines[-3:] == pic.lines[-3:] and half.lines[0] != pic.lines[0]
print("ALL OK")
