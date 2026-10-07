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
e = pic.faded("edges", 50, 20, 50)
assert e is pic.faded("edges", 50, 20, 50), "kept, not redone every frame"
assert (e.height, e.width) == (pic.height, pic.width)
inked = lambda p, r: sum(ch != " " for ch in p.lines[r])
# the top rows thin out (some cells go, some turn to shades); the rest is untouched
assert inked(e, 0) < inked(pic, 0)
assert any(ch in "░▒▓" for ch in e.lines[1] + e.lines[2])
assert e.lines[-1][-30:] == pic.lines[-1][-30:] and e._codes[-1][-30:] == pic._codes[-1][-30:]
# the left side thins out too
assert sum(e.lines[r][0] != " " for r in range(e.height)) < sum(pic.lines[r][0] != " " for r in range(pic.height))
# a shade takes the colour it replaced, as its ink, with no background
for r in range(e.height):
    for c, ch in enumerate(e.lines[r]):
        if ch in "░▒▓" and pic.lines[r][c] != ch:
            assert "\x1b[48;" not in e._codes[r][c] and "38;" in e._codes[r][c]
# corner (at 50%): the bottom right corner stays, the far corner goes
k = pic.faded("corner", 50, 20, 50)
assert k.lines[-1][-10:] == pic.lines[-1][-10:]
far_part = lambda p: sum(ch not in " ░▒▓" for ch in p.lines[0][:p.width // 3])
assert inked(k, 0) < inked(pic, 0) and far_part(k) < far_part(pic) / 2
# a smaller round fade keeps more
assert sum(inked(pic.faded("corner", 50, 20, 40), r) for r in range(pic.height)) > \
    sum(inked(k, r) for r in range(pic.height))
# on a screen wider than the picture it grows - and the grown one fades too
# (it lost the "has backgrounds" flag once, so wide windows got no fade)
wide = pic.wider(pic.width + 80)
assert wide is not pic and wide.back
assert wide.faded("edges", 50, 20, 50) is not wide
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
assert (s.art_fade, s.fade_top, s.fade_side, s.fade_round, s.fade_start) == ("edges", 50, 20, 50, 100)
s.apply({"fade_start": 40}); assert s.fade_start == 40
s.apply({"fade_start": 0}); assert s.fade_start == 40, "0 is not a start"
s = Settings()
assert ART_FADES[0] == "edges"
s.apply({"art_fade": "corner", "fade_top": 50, "fade_side": 30, "fade_round": 50})
assert (s.art_fade, s.fade_top, s.fade_side, s.fade_round) == ("corner", 50, 30, 50)
s = Settings(); s.apply({"art_fade": "x", "fade_top": 140, "fade_round": -5})
assert (s.art_fade, s.fade_top, s.fade_round) == ("edges", 50, 50), "out of range falls back"
items = sm.arrange(sm.build_items(App()))
rows = {it.label: it for it in items if it.section == "art fade"}
assert list(rows) == ["fade", "fade start", "fade top", "fade side", "fade round"], list(rows)
assert not any(it.section == "art" and "fade" in it.label for it in items), "fade has its own tab"
assert rows["fade start"].value() == "100%"
assert rows["fade top"].value() == "50%" and rows["fade round"].value() == "50%"
a = App(); a.styles()
assert console._decor["fade"] == ("edges", 50, 20, 50, 100)
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
half = pic.faded("edges", 30, 0, 50)
assert half.lines[-3:] == pic.lines[-3:] and half.lines[0] != pic.lines[0]
# each fade is a strength: 0% leaves the art alone, 100% leaves none of it,
# and in between, more is always less art
ink = lambda p: sum(ch != " " for l in p.lines for ch in l)
for mode, args in (("edges", lambda v: (v, 0, 50)), ("edges", lambda v: (0, v, 50)),
                   ("corner", lambda v: (50, 20, v))):
    got = [ink(pic.faded(mode, *args(v))) for v in range(0, 101, 10)]
    assert got[0] == ink(pic) and pic.faded(mode, *args(0)).lines == pic.lines, (mode, got)
    assert got[-1] == 0, (mode, got)
    assert all(a >= b for a, b in zip(got, got[1:])) and got[5] > got[9], (mode, got)
# fade start: only that share of the picture fades, the rest stays whole,
# and the fade stays a strength inside it
for mode, edge in (("edges", lambda p: p.lines[:6]), ("corner", lambda p: [l[:30] for l in p.lines[:6]])):
    third = pic.faded(mode, 70, 0, 70, 30)
    near = lambda p: [l[p.width // 3:] for l in p.lines[p.height // 2:]]   # the half far from the fade
    assert near(third) == near(pic), mode
    assert edge(third) != edge(pic), mode
    assert ink(pic.faded(mode, 100, 0, 100, 30)) < ink(third), mode
    assert ink(third) > ink(pic.faded(mode, 70, 0, 70, 100)), "a shorter fade keeps more"
    assert pic.faded(mode, 0, 0, 0, 30).lines == pic.lines
assert pic.faded("edges", 50, 20, 50, 30) is not pic.faded("edges", 50, 20, 50, 60)
print("ALL OK")
