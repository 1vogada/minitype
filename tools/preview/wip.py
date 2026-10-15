"""Render scenes straight from a checkout's tools/art_wow*.py, in each
scene's own theme (as make_revamp.build_wow does), to one PNG.

    MT_ROOT=<checkout> python wip.py OUT.png name [name ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apppng                                   # noqa: E402  (sets sys.path from MT_ROOT)
import art_combined as ac                       # noqa: E402
import art_wow                                  # noqa: E402

ROWS = int(os.environ.get("ROWS", "28"))


def cells(name):
    make = art_wow.WOW[name]
    pal = ac.Palette(make(ac.Palette("default")).theme)
    lines, parts, tones, bp, bt, _ = ac.render(make(pal), ROWS, pal)
    rgb = dict(pal.colours)
    rows = []
    for r, line in enumerate(lines):
        row = []
        for c, ch in enumerate(line):
            fg = rgb.get((parts[r][c], tones[r][c])) if parts[r][c] != " " else None
            bg = rgb.get((bp[r][c], bt[r][c])) if bp[r][c] != " " else None
            row.append((ch, fg, bg))
        rows.append(row)
    return rows, pal.ground


if __name__ == "__main__":
    pics = []
    for name in sys.argv[2:]:
        try:
            pics.append(cells(name))
            print("ok", name)
        except Exception as e:                 # a scene mid-edit
            print("FAILED", name, type(e).__name__, e)
    if pics:
        apppng.draw(pics, sys.argv[1])
