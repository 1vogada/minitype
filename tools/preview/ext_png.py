"""A picture with its drawn extension (above and left), as one PNG.
python ext_png.py OUT.png name [name ...]   (env ROWS=28, SCALE=1, MT_ROOT)"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apppng                          # noqa: E402
import art_combined as ac              # noqa: E402
import art_extend                      # noqa: E402
import art_wow                         # noqa: E402

ROWS = int(os.environ.get("ROWS", "28"))


def canvas(name):
    make = art_wow.WOW[name]
    pal = ac.Palette(make(ac.Palette("default")).theme)
    pic, ext = art_extend.render_ext(make(pal), ROWS, pal)
    rgb = dict(pal.colours)
    lines, parts, tones, bp, bt, _ = pic
    left, up, top, side = ext
    grid = [list(zip(*[top[k][r] for k in range(5)])) for r in range(up)]
    for r in range(len(lines)):
        grid.append(list(zip(*[side[k][r] for k in range(5)]))
                    + list(zip(lines[r], parts[r], tones[r], bp[r], bt[r])))
    out = []
    for row in grid:
        cells = []
        for ch, p, t, b, u in row:
            fg = rgb.get((p, t)) if p != " " else None
            bg = rgb.get((b, u)) if b != " " else None
            cells.append((ch, fg, bg))
        out.append(cells)
    return out, pal.ground, left, up


if __name__ == "__main__":
    pics = []
    for name in sys.argv[2:]:
        t = time.time()
        rows, ground, left, up = canvas(name)
        print(name, f"{time.time() - t:.1f}s", "left", left, "up", up)
        pics.append((rows, ground))
    apppng.draw(pics, sys.argv[1])
