"""The "upscaled" art style's renderer: a scene drawn in truecolour.

The revamp pictures (tools/art_combined.py) give every cell a glyph and two
colours out of the theme's art palette - 70 colours, gradients carried by
░▒▓ mixes of neighbouring ones. This draws the same scenes with the exact
colour of every cell: the scene sampled 4 x 8 per cell (each sample itself
the mean of 2 x 2 points, so edges are anti-aliased), and per cell the
glyph whose split of those samples fits best, with the mean colour of each
side. A sky is then a smooth gradient instead of bands and grain, an edge
gets precisely its two colours, and subtle shading inside a subject shows.

Same scenes, same sizes, same lines and text as the revamp pictures; only
the colour of every cell is free. draw() mirrors art_combined.draw (any
window of cells in the picture's own grid) so the picture can be extended
the same way (tools/art_extend.py).
"""
import math

import art_combined as ac
from art_combined import BRAILLE_BITS, MASKS, SX, SY, dist, mix

N = SX * SY
EDGE_COST = 12          # an edge glyph must beat a solid colour by this much a sample
AA = ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75))   # 2 x 2 points a sample


def _mean(cols):
    n = len(cols)
    return (sum(c[0] for c in cols) / n, sum(c[1] for c in cols) / n, sum(c[2] for c in cols) / n)


def encode(samples):
    """(character, foreground, background) drawing these 32 samples best:
    a solid colour, or an edge glyph with each side's mean colour."""
    mean = _mean(samples)
    err = sum(dist(s, mean) for s in samples)
    # a flat colour is a full block in it, as in the revamp pictures (a
    # blank would be trimmed off the end of a row as empty)
    best = (err, "█", mean, None)
    if err < N * 40:                       # all alike: a flat colour
        return best[1:]
    for ch, mask in MASKS:
        inside = set(mask)
        a = [samples[i] for i in mask]
        b = [samples[i] for i in range(N) if i not in inside]
        ma, mb = _mean(a), _mean(b)
        e = sum(dist(s, ma) for s in a) + sum(dist(s, mb) for s in b) + N * EDGE_COST
        if e < best[0]:
            best = (e, ch, ma, mb)
    return best[1:]


def draw(scene, rows, pal, row_range, col_range, texts):
    """The cells of rows `row_range` and columns `col_range` (in the
    picture's own grid, as art_combined.draw) in truecolour: (chars,
    foreground rgb, background rgb, focus) lists of rows; a colour is an
    (r, g, b) of ints or None."""
    unit, cw, cols, x_left = ac.geometry(scene, rows)
    ground = pal.ground
    r_lo, c_lo = row_range.start, col_range.start
    h, w = len(row_range), len(col_range)

    dots = {}
    for points, colour, foc, hidden in scene.lines(rows):
        pts = [((x - x_left) / cw * 2, y / unit * 4) for x, y in points]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            steps = max(1, int(max(abs(bx - ax), abs(by - ay)) * 2))
            for st in range(steps + 1):
                t = st / steps
                R, C = math.floor(ay + (by - ay) * t), math.floor(ax + (bx - ax) * t)
                if not (r_lo * 4 <= R < row_range.stop * 4 and c_lo * 2 <= C < col_range.stop * 2):
                    continue
                x, y = x_left + (C + 0.5) / 2 * cw, (R + 0.5) / 4 * unit
                if hidden and hidden(x, y):
                    continue
                dots[(R, C)] = (colour(x, y) if callable(colour) else colour, foc)

    chars = [[" "] * w for _ in range(h)]
    fgs = [[None] * w for _ in range(h)]
    bgs = [[None] * w for _ in range(h)]
    focus = [[False] * w for _ in range(h)]
    for r in row_range:
        for c in col_range:
            samples, foc_cell = [], False
            for j in range(SY):
                for i in range(SX):
                    acc = [0.0, 0.0, 0.0]
                    for ox, oy in AA:
                        x = x_left + (c + (i + ox) / SX) * cw
                        y = (r + (j + oy) / SY) * unit
                        rgb, a, foc, _ = scene.field(x, y)
                        foc_cell = foc_cell or (foc and a > 0)
                        col = mix(ground, rgb, a) if a < 1 else rgb
                        acc[0] += col[0]
                        acc[1] += col[1]
                        acc[2] += col[2]
                    samples.append((acc[0] / 4, acc[1] / 4, acc[2] / 4))
            mean = _mean(samples)
            rr, cc = r - r_lo, c - c_lo
            focus[rr][cc] = foc_cell
            text = texts.get((r, c))
            if text:
                ch, rgb, foc = text
                chars[rr][cc], fgs[rr][cc], bgs[rr][cc] = ch, rgb, mean
                focus[rr][cc] = foc_cell or foc
                continue
            cell_dots = [(dy, dx, dots[(r * 4 + dy, c * 2 + dx)]) for dy in range(4) for dx in (0, 1)
                         if (r * 4 + dy, c * 2 + dx) in dots]
            if cell_dots:
                bits = 0
                for dy, dx, (rgb, foc) in cell_dots:
                    bits |= BRAILLE_BITS[dy][dx]
                    focus[rr][cc] = focus[rr][cc] or foc
                chars[rr][cc] = chr(0x2800 + bits)
                fgs[rr][cc] = _mean([d[2][0] for d in cell_dots])
                bgs[rr][cc] = mean
                continue
            ch, fg, bg = encode(samples)
            chars[rr][cc], fgs[rr][cc], bgs[rr][cc] = ch, fg, bg
    rnd = lambda c: None if c is None else tuple(int(round(v)) for v in c)
    return (["".join(row) for row in chars], [[rnd(c) for c in row] for row in fgs],
            [[rnd(c) for c in row] for row in bgs], focus)


def render(scene, rows, pal):
    """The scene `rows` tall in truecolour: (lines, foreground, background,
    keep), its empty top rows dropped like the revamp pictures."""
    unit, cw, cols, x_left = ac.geometry(scene, rows)
    texts = {(r, c): (ch, rgb, foc) for c, r, ch, rgb, foc in scene.texts(rows, x_left, cw, unit)
             if 0 <= r < rows and 0 <= c < cols}
    lines, fg, bg, focus = draw(scene, rows, pal, range(rows), range(cols), texts)
    keep = tuple(next((c for c in range(cols) if focus[r][c]), cols) for r in range(rows))
    return lines, fg, bg, keep
