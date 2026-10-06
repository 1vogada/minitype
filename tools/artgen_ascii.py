"""Shape-matched ASCII rendering of artgen scenes: the "detailed" style.

A character has a shape, not just a darkness: "_" is ink along the bottom
of its cell, "'" a speck at the top, "d" fills the lower right. Every
cell is sampled on the same 4 x 8 grid the font's characters were
measured on (tools/glyphs.py, from the terminal font itself), and

  * inside a shape, the material's own ramp shades it by tone (its
    texture: sand, needles, water...),
  * on a shape's edge, the character whose ink best matches the part of
    the cell the shape covers is used, so outlines run smoothly through
    the cells instead of stepping (d b P Y, _ ¯ - , ' ` / \\ ( ) ...),
  * a line is drawn into the cell as a thin stroke and matched against
    line characters only, so it lands on the right height in the cell:
    gentle slopes come out as  _,.-'"^  and steep ones as  / | \\ ( ).

Text (stamps) stays exactly as written.
"""

from artgen import Layer, Line, Stamp, _trim, _digit, SPAN_COLS
import glyphs

SX, SY = glyphs.COLS, glyphs.ROWS          # samples per cell = glyph patches
N = SX * SY

_SHAPES = glyphs.load()
# the edge of a filled shape: punctuation, and the few letters ASCII
# artists shape with (d b P Y o), never ones that read as words
FILL_SET = " .,:;'`\"-_=+~^*|/\\()[]<>o"
# lines and outlines, by which way they run (on screen): the characters
# that run that way, from which the shape picks the one at the right
# height in the cell - so gentle slopes step  _,.-'"^  as artists draw them
FLAT = " _-¯.'`,"
RISING = " /,.'_-¯`\""        # going up to the right
STEEP_R = " /|"
FALLING = " \\`'._-¯,\""      # going down to the right
STEEP_F = " \\|"
UPRIGHT = " |()"
_MAX = [max(_SHAPES[c][r][k] for c in _SHAPES) or 1.0 for r in range(SY) for k in range(SX)]


def _vec(ch):
    """A character's shape, each patch scaled by the most ink any
    character has there, so every part of the cell counts the same."""
    flat = [v for row in _SHAPES[ch] for v in row]
    return [v / m for v, m in zip(flat, _MAX)]


def _blur(v):
    """A shape softened a patch each way, so a stroke a patch off still
    looks like the character for it (alignment-insensitive matching, as
    in Xu, Zhang and Wong's structure-based ASCII art)."""
    out = []
    for j in range(SY):
        for i in range(SX):
            tot = wt = 0.0
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    jj, ii = j + dj, i + di
                    if 0 <= jj < SY and 0 <= ii < SX:
                        w = 1.0 if (di, dj) == (0, 0) else 0.5 if di == 0 or dj == 0 else 0.25
                        tot += v[jj * SX + ii] * w
                        wt += w
            out.append(tot / wt)
    return out


def _pool(chars, blank=True):
    """(character, shape, softened shape) for each; without blank, no
    space (a line always shows)."""
    return [(c, _vec(c), _blur(_vec(c))) for c in dict.fromkeys(chars)
            if c in _SHAPES and (blank or c != " ")]


_FILL = _pool(FILL_SET)
# outlines: the line characters (and for bold materials the chunky corners)
OUTLINE_SET = " _-¯'.,`\"=|/\\()<>[]~^"
_OUTLINE = _pool(OUTLINE_SET, blank=False)
_OUTLINE_BOLD = _pool(OUTLINE_SET + "dbPY", blank=False)
_FILL_BOLD = _pool(FILL_SET + "dbPY")
POOLS = {k: _pool(v, blank=False) for k, v in (("flat", FLAT), ("rising", RISING), ("steep_r", STEEP_R),
                                   ("falling", FALLING), ("steep_f", STEEP_F),
                                   ("upright", UPRIGHT))}
POOLS_OUTLINE = {k: _pool(v, blank=False) for k, v in (("flat", FLAT), ("rising", RISING),
                                                     ("steep_r", STEEP_R), ("falling", FALLING),
                                                     ("steep_f", STEEP_F), ("upright", UPRIGHT))}


def way(dx, dy):
    """Which pool a run going (dx, dy) belongs to (y down, square units)."""
    if dx < 0:
        dx, dy = -dx, -dy
    if dx == 0 and dy == 0:
        return "flat"
    slope = abs(dy) / (dx or 1e-9)
    if slope < 0.4:
        return "flat"
    if slope > 3.0:
        return "upright"
    rising = dy < 0
    if slope < 1.2:
        return "rising" if rising else "falling"
    return "steep_r" if rising else "steep_f"
_DENSITY = {c: sum(v) / N for c, v in ((c, _vec(c)) for c in _SHAPES)}
_cache = {}


def best(target, pool):
    """The character in pool whose shape is nearest the target; on a near
    tie the plainer one (less ink), so edges stay clean."""
    key = (id(pool), tuple(round(v * 6) for v in target))
    hit = _cache.get(key)
    if hit is None:
        soft = _blur(target)
        # exact shape, plus the softened one so near misses still match
        hit = min(pool, key=lambda g: sum((a - b) ** 2 for a, b in zip(target, g[1]))
                  + 2 * sum((a - b) ** 2 for a, b in zip(soft, g[2]))
                  + 0.25 * sum(g[1]) / N)[0]
        _cache[key] = hit
    return hit


def density(mat, tone, r=0, c=0):
    """How much ink the material's interior has at this tone, 0..1."""
    ch = mat.char(tone, r, c)
    return _DENSITY.get(ch, 0.0)


class _Grid:
    """The scene sampled SX x SY times a cell: the front layer at each
    sample (None for nothing)."""

    def __init__(self, scene, rows):
        self.rows = rows
        self.unit = unit = 1.0 / rows
        self.cw = cw = unit / 2
        aspect = scene.aspect_of(rows)
        box_cols = max(1, round(aspect / cw))
        self.cols = cols = max(box_cols, SPAN_COLS) if scene.span else box_cols
        self.x_left = x_left = aspect - cols * cw
        self.items = scene.parts_of(rows)
        self.layers = [p for p in self.items if isinstance(p, Layer)]
        self.order = {id(p): z for z, p in enumerate(self.items)}
        self.owner = owner = {}
        for li, layer in enumerate(self.layers):
            x0, y0, x1, y1 = layer.shape.box
            c0 = max(0, int((x0 - x_left) / cw) - 1)
            c1 = min(cols, int((x1 - x_left) / cw) + 2)
            r0, r1 = max(0, int(y0 / unit) - 1), min(rows, int(y1 / unit) + 2)
            test = layer.shape.test
            for r in range(r0, r1):
                for c in range(c0, c1):
                    cell = owner.get((r, c))
                    for j in range(SY):
                        y = (r + (j + 0.5) / SY) * unit
                        for i in range(SX):
                            x = x_left + (c + (i + 0.5) / SX) * cw
                            if test(x, y):
                                if cell is None:
                                    cell = owner[(r, c)] = [None] * N
                                cell[j * SX + i] = li

    def at(self, c, r, fx=0.5, fy=0.5):
        return self.x_left + (c + fx) * self.cw, (r + fy) * self.unit


def _inside(g, li, r, c, k):
    """Whether sample k of cell (r, c) has layer li all round it (so it's
    not on the layer's boundary)."""
    j, i = divmod(k, SX)
    for dj, di in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        jj, ii, rr, cc = j + dj, i + di, r, c
        if jj < 0:
            jj, rr = SY - 1, r - 1
        elif jj >= SY:
            jj, rr = 0, r + 1
        if ii < 0:
            ii, cc = SX - 1, c - 1
        elif ii >= SX:
            ii, cc = 0, c + 1
        cell = g.owner.get((rr, cc))
        if cell is None or cell[jj * SX + ii] != li:
            return False
    return True


def _grazes(strokes, r, c, z):
    """Whether a neighbouring cell carries more of the same line."""
    here = strokes[(r, c)][3]
    mine = (here[0] ** 2 + here[1] ** 2) ** 0.5
    for dr, dc in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        other = strokes.get((r + dr, c + dc))
        if other and other[1] == z and (other[3][0] ** 2 + other[3][1] ** 2) ** 0.5 > mine:
            return True
    return False


def _across(cx, cy, dx, dy):
    """A stroke right across a cell through (cx, cy) (in samples) running
    (dx, dy): a line always spans the character it's drawn with, so a
    short one still gets the full  / | \\ _  rather than a speck."""
    d = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / d, dy / d
    out = [0.0] * N
    for k in range(-24, 25):
        t = k / 3
        x, y = cx + ux * t, cy + uy * t
        i, j = int(x), int(y)
        if 0 <= i < SX and 0 <= j < SY:
            out[j * SX + i] = 1.0
    return out


def render(scene, rows, raw=False):
    """The scene `rows` tall in shape-matched ASCII: (lines, parts, tones,
    keep), like artgen.render. With raw, the whole canvas untrimmed: rows
    of characters, colour letters and tones, every row the full width."""
    g = _Grid(scene, rows)
    cols, layers, order = g.cols, g.layers, g.order
    chars = [[" "] * cols for _ in range(rows)]
    parts = [[" "] * cols for _ in range(rows)]
    tones = [[" "] * cols for _ in range(rows)]
    focus = [[False] * cols for _ in range(rows)]
    zof = [[-1] * cols for _ in range(rows)]

    for (r, c), cell in g.owner.items():
        counts = {}
        for li in cell:
            if li is not None:
                counts[li] = counts.get(li, 0) + 1
        if not counts:
            continue
        total = sum(counts.values())
        # the layer this cell shows: the one covering most of it
        li = max(counts, key=lambda k: (counts[k], order[id(layers[k])]))
        layer, mat = layers[li], layers[li].mat
        tone = layer.tone(*g.at(c, r))
        mine = counts[li]
        part = mat.part(tone)
        if total < 3:
            continue                                   # a speck of something: leave it
        if mat.code and tone < mat.code_below:
            ch = mat.char(tone, r, c)
        elif mat.outline and 3 <= mine <= N - 3 and (mat.bold or mine < N * 0.6):
            # the edge of an outlined shape, whatever is behind it: the
            # outline character shaped like the part it covers
            ch = best([1.0 if s_ == li else 0.0 for s_ in cell], _OUTLINE_BOLD if mat.bold else _OUTLINE)
            part = mat.outline
        elif total >= N - 2 or not mat.edges or mat.dither:
            # covered (by this layer or with others): its own texture, so
            # textures carry on right up to where they meet
            ch = mat.char(tone if total >= N - 2 else tone * total / N, r, c)
        elif total >= N * 0.6:
            ch = mat.char(tone * 0.85, r, c)           # mostly covered: just shaded lighter
        else:
            # the edge of everything here: shaped like what's covered
            ch = best([0.0 if s_ is None else 1.0 for s_ in cell], _FILL_BOLD if mat.bold else _FILL)
        if ch == " ":
            continue
        chars[r][c], parts[r][c], tones[r][c] = ch, part, _digit(tone)
        focus[r][c], zof[r][c] = layer.focus, order[id(layer)]

    # lines: a thin stroke through each cell, matched against line glyphs
    strokes = {}                                   # (r, c) -> [32 coverage], z, part, tone, focus
    for p in g.items:
        if not isinstance(p, Line):
            continue
        z = order[id(p)]
        pts = [((x - g.x_left) / g.cw * SX, y / g.unit * SY) for x, y in p.points]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            steps = max(1, int(max(abs(bx - ax), abs(by - ay)) * 2))
            for st in range(steps + 1):
                t = st / steps
                X, Y = ax + (bx - ax) * t, ay + (by - ay) * t
                c, r = int(X // SX), int(Y // SY)
                if not (0 <= r < rows and 0 <= c < cols):
                    continue
                cell = strokes.get((r, c))
                if cell is None or cell[1] < z:
                    cell = strokes[(r, c)] = [[0.0, 0.0, 0], z, p, [0.0, 0.0]]
                elif cell[1] > z:
                    continue
                fx, fy = (bx - ax, by - ay) if bx >= ax else (ax - bx, ay - by)
                cell[3][0] += fx / steps          # its way through the cell, left to right
                cell[3][1] += fy / steps
                cell[0][0] += X - c * SX           # where it runs in the cell
                cell[0][1] += Y - r * SY
                cell[0][2] += 1
    for (r, c), ((sx, sy, n), z, p, (dx, dy)) in strokes.items():
        if z <= zof[r][c]:
            continue
        # a line that only grazes the cell is drawn by its neighbour; one
        # character per step keeps it one character wide
        if (dx * dx + dy * dy) ** 0.5 < 1.6 and _grazes(strokes, r, c, z):
            continue
        ch = p.char or best(_across(sx / n, sy / n, dx, dy), POOLS[way(dx, dy)])
        if ch == " ":
            continue
        chars[r][c], parts[r][c], tones[r][c] = ch, p.part, _digit(p.tone)
        focus[r][c], zof[r][c] = p.focus, z

    for p in g.items:
        if isinstance(p, Stamp):
            z = order[id(p)]
            c0, r = int((p.x - g.x_left) / g.cw), int(p.y / g.unit)
            for k, ch in enumerate(p.text):
                c = c0 + k
                if 0 <= r < rows and 0 <= c < cols and ch != " " and z > zof[r][c]:
                    chars[r][c], parts[r][c] = ch, p.part_at(k).strip() or "a"
                    tones[r][c] = _digit(p.tone)
                    focus[r][c], zof[r][c] = p.focus, z

    if raw:
        return chars, parts, tones
    (lines, pparts, ptones), keep = _trim(scene, [chars, parts, tones], focus)
    return lines, pparts, ptones, keep
