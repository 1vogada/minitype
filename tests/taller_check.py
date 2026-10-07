"""Filler on top of the art: the picture is placed by its own height, and
rows of its sky carry on above it where there's room (for the fade to
dissolve into, and so it doesn't stop on a straight line)."""
import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
from minitype.terminal import console, style
from minitype.terminal.art import paint, revamp, TALLER

pal = style.Styles("ocean").art_palette(True)
pic = paint(revamp("island")[0], pal)
assert pic.back and pic.extra == 0
assert pic.taller(0) is pic
t = pic.taller(6)
assert t is pic.taller(6), "kept, not redone every frame"
assert (t.height, t.extra, t.width) == (pic.height + 6, 6, pic.width)
assert t.lines[6:] == pic.lines and t._codes[6:] == list(pic._codes), "the picture itself untouched"
assert t.keep[:6] == (pic.width,) * 6 and t.keep[6:] == pic.keep, "filler is scenery, no subject"
assert all(len(l) == t.width for l in t.lines[:6])
# solid sky in the picture's own colours (truecolour), no blanks
assert all(ch != " " for l in t.lines[:6] for ch in l)
assert all("38;2;" in c for row in t._codes[:6] for c in row)
# just above the seam the colours are the top edge's own; higher up they even out
import re


def rough(r):
    """How much the sky's colour jumps from one column to the next along
    filler row r (stars and specks left out)."""
    rgb = [tuple(map(int, re.search(r"38;2;(\d+);(\d+);(\d+)", c).groups()))
           for ch, c in zip(t.lines[r], t._codes[r]) if ch == "█"]
    return sum(sum(abs(x - y) for x, y in zip(a, b)) for a, b in zip(rgb, rgb[1:]))
assert rough(0) < rough(5), (rough(0), rough(5))
# taller then wider, wider then taller, faded: they all keep the filler
w = pic.wider(pic.width + 40).taller(4)
assert w.width == pic.width + 40 and w.extra == 4 and w.height == pic.height + 4
f = t.faded("edges", 50, 20, 50)
assert f.extra == 6 and f.height == t.height
# pictures without backgrounds get none
d = paint(revamp("island")[0], pal)
d2 = object.__new__(type(d)); d2.__dict__.update(d.__dict__); d2.back = False
assert d2.taller(5) is d2

# drawn: as many filler rows as there's room for, up to TALLER of its height
console._decor["fade"] = None
W = pic.width + 2
for H, want in ((pic.height + 2, 1), (pic.height + 6, 5), (200, int(pic.height * TALLER))):
    rows = console.overlay_art([""] * H, [pic], W, 0, True)
    drawn = sum(1 for r in rows if r)
    assert drawn == pic.height + want, (H, drawn, want)
# no room at all: the picture still fits by its own height, with no filler
rows = console.overlay_art([""] * (pic.height + 1), [pic], W, 0, True)
assert sum(1 for r in rows if r) == pic.height
# too short for the picture itself: nothing (the filler doesn't make it fit)
rows = console.overlay_art([""] * pic.height, [pic], W, 0, True)
assert not any(rows)
# beside text, the filler keeps to the right of it like the picture does
rows = ["  some menu text here"] * 12 + [""] * 60
out = console.overlay_art(rows, [pic], W + 60, 0, False)
assert all(r.startswith("  some menu text here") for r in out[:12])
assert sum(1 for r in out if len(r) > 30) >= pic.height + 1
print("ALL OK")
