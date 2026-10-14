"""The "upscaled" art style: a scene drawn at braille resolution.

The other styles sample a cell a few times and pick one of a small set of
glyphs. This one works on the dot grid a braille character is made of -
2 x 4 dots per cell - so it decides eight separate marks per cell, and gives
the cell the two colours that fit it best.

Per cell:
  - measure each of the 8 dots over its own area of the cell
  - for every pair of palette colours, assign each dot to whichever of the
    two is nearer (measured along the line between them, so the split is the
    pair's own midpoint) - that assignment is a braille pattern, or a block
    shape when one covers exactly those dots
  - keep the pair, pattern and colours that reproduce the cell most closely

A clean block shape scores better than it measures, so a straight edge or a
trunk stays a bar instead of breaking into dots; dots are kept for cells
that are genuinely intricate. Where a cell is a smooth blend of two colours -
a sky gradient - a shade (░▒▓) of them wins on its own.

Stored exactly like the other styles: per cell a glyph, a foreground palette
key and a background palette key. A cell never uses a character outside
blocks, block elements, shades and braille, except a text glyph the scene
itself asked for.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..")]

import art_combined as ac          # noqa: E402

# samples per cell: 2 x 4 braille dots
DOTS = 8
BRAILLE_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))


def _dot_pattern(bits):
    """Which of the 8 dots a braille pattern inks."""
    return tuple(1 if bits & BRAILLE_BITS[dy][dx] else 0
                 for dy in range(4) for dx in range(2))


# a braille glyph for every non-empty pattern
PATTERN_GLYPH = {_dot_pattern(b): chr(0x2800 + b) for b in range(1, 256)}

# Block shapes, as the dots they ink. Only shapes that ink whole dots are
# listed: a cell is drawn as 8 dots, so a glyph covering half a dot (the
# verticals ▏▎▍▋▊▉▕, and the single-row ▔) cannot be drawn exactly and is
# left to the dot patterns.
_HALF = {(1, 0, 0, 0): "▘", (0, 1, 0, 0): "▝", (0, 0, 1, 0): "▖", (0, 0, 0, 1): "▗",
         (1, 1, 0, 0): "▀", (0, 0, 1, 1): "▄", (1, 0, 1, 0): "▌", (0, 1, 0, 1): "▐",
         (1, 0, 0, 1): "▚", (0, 1, 1, 0): "▞", (1, 1, 1, 0): "▛", (1, 1, 0, 1): "▜",
         (1, 0, 1, 1): "▙", (0, 1, 1, 1): "▟", (1, 1, 1, 1): "█"}
BLOCK_PATTERNS = {}
for _q, _ch in _HALF.items():
    # a quadrant is the 2 x 2 dot block at its corner
    _pat = tuple(1 if _q[(1 if dy > 1 else 0) * 2 + dx] else 0
                 for dy in range(4) for dx in range(2))
    BLOCK_PATTERNS.setdefault(_pat, []).append(_ch)
for _n, _ch in enumerate("▁▂▃▅▆▇", 1):
    # the eighths fill 2n of the 16 coverage rows, which is a whole number of
    # dots only for n up to 4 (▁▂▃▄); ▅▆▇ cut a dot in half
    if 2 * _n % 4:
        continue
    _rows = 2 * _n // 4
    _pat = tuple(1 if dy >= 4 - _rows else 0 for dy in range(4) for dx in range(2))
    BLOCK_PATTERNS.setdefault(_pat, []).append(_ch)

# shades: a flat blend of the two colours, for a smooth gradient
SHADES = ((0.25, "░"), (0.5, "▒"), (0.75, "▓"))


class Encoder:
    """Turns a scene into upscaled picture data, in a theme's palette."""

    def __init__(self, palette, shape_bonus=1.8):
        self.pal = palette
        self.entries = list(palette.colours)             # ((letter, tone), rgb)
        self.keys = [e[0] for e in self.entries]
        self.rgbs = [e[1] for e in self.entries]
        # how much a clean block shape is preferred over a dot pattern that
        # measures the same; 1.0 would be no preference
        self.shape_bonus = shape_bonus

    def cell(self, dots):
        """(glyph, foreground key, background key) for one cell's 8 dots."""
        n = len(self.rgbs)
        cost = [[ac.dist(d, r) for r in self.rgbs] for d in dots]
        # the colours worth pairing: those nearest the cell's own dots
        pool = set()
        for i in range(DOTS):
            ci = cost[i]
            pool.update(sorted(range(n), key=ci.__getitem__)[:6])
        pool = sorted(pool)
        best = None
        for ai, a in enumerate(pool):
            ra = self.rgbs[a]
            ca = [t[a] for t in cost]
            for b in pool[ai + 1:]:
                rb = self.rgbs[b]
                cb = [t[b] for t in cost]
                dx, dy, dz = rb[0] - ra[0], rb[1] - ra[1], rb[2] - ra[2]
                err, pat = 0.0, []
                for i, c in enumerate(dots):
                    if ((c[0] - ra[0]) * dx + (c[1] - ra[1]) * dy + (c[2] - ra[2]) * dz) > 0:
                        pat.append(1)
                        err += cb[i]
                    else:
                        pat.append(0)
                        err += ca[i]
                if not any(pat):
                    continue
                pat = tuple(pat)
                hit = BLOCK_PATTERNS.get(pat)
                if hit:
                    ch, scored = hit[0], err / self.shape_bonus
                else:
                    ch, scored = PATTERN_GLYPH.get(pat), err
                if ch and (best is None or scored < best[0]):
                    best = (scored, ch, self.keys[b], self.keys[a])
        # a cell that is one flat tone
        for k in pool:
            e = sum(cost[i][k] for i in range(DOTS))
            if best is None or e < best[0]:
                best = (e, "█", self.keys[k], self.keys[k])
        # a smooth blend of two colours, which is what a sky gradient is
        for ai, a in enumerate(pool):
            ra = self.rgbs[a]
            for b in pool[ai + 1:]:
                rb = self.rgbs[b]
                for blend, ch in SHADES:
                    mx = (rb[0] + (ra[0] - rb[0]) * blend,
                          rb[1] + (ra[1] - rb[1]) * blend,
                          rb[2] + (ra[2] - rb[2]) * blend)
                    err = sum(ac.dist(d, mx) for d in dots)
                    if err < best[0]:
                        best = (err, ch, self.keys[a], self.keys[b])
        return best[1], best[2], best[3]


def render(scene, rows, pal=None):
    """The scene at this height: (lines, parts, tones, bparts, btones, keep),
    the same shape the other renderers return."""
    pal = pal or ac.Palette(scene.theme)
    enc = Encoder(pal)
    unit = 1.0 / rows
    cw = unit / 2
    box = max(1, round(scene.aspect / cw))
    cols = max(box, ac.SPAN_COLS) if scene.span else box
    x_left = scene.aspect - cols * cw
    texts = {}
    for c, r, ch, rgb, foc in scene.texts(rows, x_left, cw, unit):
        if 0 <= r < rows and 0 <= c < cols:
            texts[(r, c)] = (ch, rgb)
    lines, parts, tones, bparts, btones = [], [], [], [], []
    focus = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        lrow, prow, trow, brow, btrow = [], [], [], [], []
        for c in range(cols):
            got = texts.get((r, c))
            if got:
                ch, rgb = got
                key = pal.nearest(rgb, ground=False)[0][0]
                lrow.append(ch)
                prow.append(key[0])
                trow.append(key[1])
                brow.append(" ")
                btrow.append(" ")
                focus[r][c] = True
                continue
            dots = []
            for dy in range(4):
                for dx in range(2):
                    acc = [0.0, 0.0, 0.0]
                    n = 0
                    # nine points across the dot, so a dot that straddles an
                    # edge gets the colour it mostly is
                    for sj in (1 / 6, 0.5, 5 / 6):
                        for si in (1 / 6, 0.5, 5 / 6):
                            x = x_left + (c + (dx + si) / 2) * cw
                            y = (r + (dy + sj) / 4) * unit
                            rgb, a, foc, tag = scene.field(x, y)
                            if foc:
                                focus[r][c] = True
                            col = ac.mix(pal.ground, rgb, a) if a < 1 else rgb
                            acc[0] += col[0]
                            acc[1] += col[1]
                            acc[2] += col[2]
                            n += 1
                    dots.append((acc[0] / n, acc[1] / n, acc[2] / n))
            ch, fk, bk = enc.cell(dots)
            lrow.append(ch)
            prow.append(fk[0] if ch != " " else " ")
            trow.append(fk[1] if ch != " " else " ")
            brow.append(bk[0] if ch != " " else " ")
            btrow.append(bk[1] if ch != " " else " ")
        lines.append("".join(lrow))
        parts.append("".join(prow))
        tones.append("".join(trow))
        bparts.append("".join(brow))
        btones.append("".join(btrow))
    width = cols
    keep = tuple(next((c for c in range(width) if focus[r][c]), width) for r in range(rows))
    return lines, parts, tones, bparts, btones, keep
