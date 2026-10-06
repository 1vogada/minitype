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
e = pic.faded("edges", 5, 12, 70)
assert e is pic.faded("edges", 5, 12, 70), "kept, not redone every frame"
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
k = pic.faded("corner", 5, 12, 60)
assert k.lines[-1][-10:] == pic.lines[-1][-10:]
assert inked(k, 0) < inked(pic, 0) / 2
# bigger round keeps more
assert sum(inked(pic.faded("corner", 5, 12, 100), r) for r in range(pic.height)) > \
    sum(inked(k, r) for r in range(pic.height))
# pictures without backgrounds (ASCII) are left alone when drawn
app = App(); app.settings.theme = "forest"; app.settings.art_style = "detailed"; app.styles()
console.term_size = lambda: (150, 42)
d = console._decor["art"][0]
assert not d.back

# ---------------------------------------------------------------- settings
s = Settings()
assert (s.art_fade, s.fade_top, s.fade_side, s.fade_round) == ("edges", 5, 12, 70)
assert ART_FADES[0] == "edges"
s.apply({"art_fade": "corner", "fade_top": 8, "fade_side": 24, "fade_round": 50})
assert (s.art_fade, s.fade_top, s.fade_side, s.fade_round) == ("corner", 8, 24, 50)
s = Settings(); s.apply({"art_fade": "x", "fade_top": 7, "fade_round": 5})
assert (s.art_fade, s.fade_top, s.fade_round) == ("edges", 5, 70)
rows = {it.label: it for it in sm.build_items(App())}
for label in ("art fade", "fade top", "fade side", "fade round"):
    assert rows[label].section == "art", label
assert rows["fade top"].value() == "5 rows" and rows["fade round"].value() == "70%"
a = App(); a.styles()
assert console._decor["fade"] == ("edges", 5, 12, 70)
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
print("ALL OK")
