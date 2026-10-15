"""Revamp vs truecolour for the same scenes, one under the other.
python tc_vs.py OUT.png name [name ...]   (env ROWS=28, SCALE=2, LAST=cols)"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apppng                     # noqa: E402
import art_combined as ac         # noqa: E402
import art_truecolor as tc        # noqa: E402
import art_wow                    # noqa: E402

ROWS = int(os.environ.get("ROWS", "28"))
LAST = int(os.environ.get("LAST", "0"))


def cut(rows):
    return [r[-LAST:] for r in rows] if LAST else rows


pics = []
for name in sys.argv[2:]:
    make = art_wow.WOW[name]
    pal = ac.Palette(make(ac.Palette("default")).theme)
    sc = make(pal)
    rgb = dict(pal.colours)
    lines, parts, tones, bp, bt, _ = ac.render(sc, ROWS, pal)
    old = [[(ch, rgb.get((p, t)) if p != " " else None, rgb.get((b, u)) if b != " " else None)
            for ch, p, t, b, u in zip(*row)] for row in zip(lines, parts, tones, bp, bt)]
    t0 = time.time()
    tl, tf, tb, _ = tc.render(sc, ROWS, pal)
    new = [[(ch, f, b) for ch, f, b in zip(*row)] for row in zip(tl, tf, tb)]
    print(name, f"truecolour {time.time() - t0:.1f}s")
    pics += [(cut(old), pal.ground), (cut(new), pal.ground)]
apppng.draw(pics, sys.argv[1])
