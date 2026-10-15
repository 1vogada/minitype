"""The scene drawn on beyond a picture (tools/art_extend.py): on a big
window the art grows left and up with the scene itself - real columns and
rows drawn when the picture was made - before any copied columns or filler.
"""
import os
import sys
import tempfile

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minitype.terminal import console, style                 # noqa: E402
from minitype.terminal.art import THEME_ART, paint, revamp, upscaled, TALLER   # noqa: E402

pal = style.Styles("synthwave").art_palette(True)
piece = revamp(THEME_ART["synthwave"])[0]
assert piece.ext, "every revamp picture carries its extension"
left, up, top, side = piece.ext
height, width = len(piece.lines), len(piece.lines[0])
assert left > 0 and up == int(height * TALLER)
assert len(top.lines) == up and all(len(l) == left + width for l in top.lines)
assert len(side.lines) == height and all(len(l) == left for l in side.lines)
assert all(k == width for k in top.keep or (width,)), "the extension is scenery"

pic = paint(piece, pal)
# wider: the drawn columns, right next to the picture, before anything else
w = pic.wider(width + 30)
assert w.width == width + 30 and w.height == height
assert all(l[30:] == p for l, p in zip(w.lines, pic.lines)), "the picture itself untouched"
assert all(l[:30] == s[-30:] for l, s in zip(w.lines, side.lines)), "the scene's own columns"
assert w.keep == tuple(k + 30 for k in pic.keep)
# past the drawn columns it grows on from its own (and keeps the drawn ones)
far = pic.wider(width + left + 25)
assert far.width == width + left + 25
assert all(l[25:25 + left] == s for l, s in zip(far.lines, side.lines))

# taller: the drawn rows above, each column the one above it on the canvas
t = pic.taller(5)
assert t.extra == 5 and t.height == height + 5
assert t.lines[5:] == pic.lines
assert list(t.lines[:5]) == [l[left:] for l in top.lines[up - 5:]], "the scene drawn above it"
assert t.keep[:5] == (width,) * 5
# grown sideways and then taller: the rows above line up with the columns
wt = pic.wider(width + 30).taller(4)
assert list(wt.lines[:4]) == [l[left - 30:] for l in top.lines[up - 4:]]
# more rows than were drawn: the drawn ones, then filler above them
more = pic.taller(up + 3)
assert more.extra == up + 3
assert list(more.lines[3:3 + up]) == [l[left:] for l in top.lines]

# on the screen: a wide window shows the drawn columns, not copies
console._decor["fade"] = None
rows = console.overlay_art([""] * (height + 3), [pic], width + 41, 0, False)
assert rows[-2], "drawn"

# beside menu text the art fills up to one straight edge past the widest
# text line - no step where the picture's own box was
text = ["  a menu line", "  a much longer menu line here", "  short"] + [""] * (height + 10)
out = console.overlay_art(text, [pic], width + 60, 0, False)
widest = max(len(line) for line in text[:3])
beside = [console.ANSI.sub("", r) for r in out[:3]]
assert any(len(p) > widest + 2 for p in beside), "the art comes up beside the text"
for plain, line in zip(beside, text[:3]):
    assert plain.startswith(line)
    if len(plain) > widest + 2:
        assert plain[len(line):widest + 2].strip() == "", ("art before the edge", plain[:widest + 4])
        assert plain[widest + 2] != " " or len(set(plain[widest + 2:])) > 1, "art from the edge"

# the upscaled style: the same scenes drawn bigger, then the revamp sizes
for name in sorted(set(THEME_ART.values())):
    big = upscaled(name)
    if not big:
        continue
    assert [len(p.lines) for p in big] == sorted((len(p.lines) for p in big), reverse=True)
    assert len(big[-1].lines) > len(revamp(name)[0].lines), name
    assert all(p.ext and p.back_parts for p in big), name
print("ALL OK")
