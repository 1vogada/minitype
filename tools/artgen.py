"""A tiny rasteriser that turns scenes made of shapes into detailed ASCII
art, for tools/make_art.py.

A scene is drawn in its own coordinates: y runs 0 (top) to 1 (bottom) and
x runs 0 to the scene's aspect, in the same units, so a circle is round
on screen. Each character cell is sampled 4x4. Cells a shape covers fully
take a character from its material's ramp by tone (shading); cells on an
edge take a character shaped like the part that's covered (d b Y P ' , ...),
which keeps outlines crisp. Lines (stems, rays) are drawn with / | \\ - by
their direction, and stamps put exact text down (stars, letters).

Colours are palette parts, one letter each: d(im) t(ext) e(rror) e(x)tra
a(ccent) g(ood) w(arn). A material can pick a different part by tone, so
shadows can be dim and highlights bright.

Spanning scenes (span=True) are drawn far to the left of their box too:
layers marked focus=False (sea, hills, sky) carry on across the whole
bottom of the screen while the focus stays in the corner.
"""

import math

SPAN_COLS = 160          # how wide a spanning scene is drawn
SUB = 4                  # samples per cell, each way

# a 4x4 ordered-dither matrix, 0..1
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
BAYER = [[(v + 0.5) / 16 for v in row] for row in BAYER]

# what each edge glyph roughly covers of its cell, 4x4 from the top left:
# "#" full, "+" half, "." a little. An edge cell takes the glyph closest
# to what's covered there.
_GLYPHS = {
    ".": ["    ", "    ", "    ", " ++ "],
    ",": ["    ", "    ", " +. ", " +  "],
    "'": ["  + ", "  + ", "    ", "    "],
    "`": [" +  ", "  . ", "    ", "    "],
    "-": ["    ", "####", "    ", "    "],
    "_": ["    ", "    ", "    ", "####"],
    '"': [" ++ ", " ++ ", "    ", "    "],
    "=": ["    ", "####", "####", "    "],
    "|": [" ## ", " ## ", " ## ", " ## "],
    "/": ["  .#", " .#.", ".#. ", "#.  "],
    "\\": ["#.  ", ".#. ", " .#.", "  .#"],
    "(": ["  #.", " #. ", " #. ", "  #."],
    ")": [".#  ", " .# ", " .# ", ".#  "],
    "<": ["  .#", ".##.", ".##.", "  .#"],
    ">": ["#.  ", ".##.", ".##.", "#.  "],
    "d": ["  ##", " ###", "####", "####"],
    "b": ["##  ", "### ", "####", "####"],
    "P": ["####", "####", "### ", "##  "],
    "Y": ["####", "####", " ###", "  ##"],
    "[": ["##  ", "##  ", "##  ", "##  "],
    "]": ["  ##", "  ##", "  ##", "  ##"],
}
GLYPHS = [(ch, [{"#": 1.0, "+": 0.5, ".": 0.25, " ": 0.0}[v] for row in rows for v in row])
          for ch, rows in _GLYPHS.items()]


BOLD = set("dbPY[]<>")        # chunky edge glyphs, for materials that want them
SOFT = [g for g in GLYPHS if g[0] not in BOLD]


def best_glyph(cover, bold=False):
    """The edge glyph closest to a cell's 4x4 coverage."""
    return min(GLYPHS if bold else SOFT,
               key=lambda g: sum((a - b) ** 2 for a, b in zip(g[1], cover)))[0]


# ---------------------------------------------------------------- shapes

class Shape:
    """A point test with a bounding box (x0, y0, x1, y1) to skip work."""

    def __init__(self, test, box):
        self.test, self.box = test, box

    def __or__(self, other):
        a, b = self.box, other.box
        return Shape(lambda x, y: self.test(x, y) or other.test(x, y),
                     (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])))

    def __sub__(self, other):
        return Shape(lambda x, y: self.test(x, y) and not other.test(x, y), self.box)

    def __and__(self, other):
        a, b = self.box, other.box
        return Shape(lambda x, y: self.test(x, y) and other.test(x, y),
                     (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))


INF = 1e9


def circle(cx, cy, r):
    return Shape(lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r,
                 (cx - r, cy - r, cx + r, cy + r))


def ellipse(cx, cy, rx, ry, angle=0.0):
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    r = max(rx, ry)

    def test(x, y):
        dx, dy = x - cx, y - cy
        u, v = dx * c + dy * s, -dx * s + dy * c
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1
    return Shape(test, (cx - r, cy - r, cx + r, cy + r))


def rect(x0, y0, x1, y1):
    return Shape(lambda x, y: x0 <= x <= x1 and y0 <= y <= y1, (x0, y0, x1, y1))


def poly(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    edges = list(zip(pts, pts[1:] + pts[:1]))

    def test(x, y):
        inside = False
        for (x1, y1), (x2, y2) in edges:
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
        return inside
    return Shape(test, (min(xs), min(ys), max(xs), max(ys)))


def below(fn, x0=-INF, x1=INF, bottom=INF):
    """Everything under the curve y = fn(x) (the ground, the sea)."""
    return Shape(lambda x, y: x0 <= x <= x1 and fn(x) <= y <= bottom,
                 (x0, -INF, x1, bottom))


def between(top, bottom, x0=-INF, x1=INF):
    """A band between two curves."""
    return Shape(lambda x, y: x0 <= x <= x1 and top(x) <= y <= bottom(x),
                 (x0, -INF, x1, INF))


def bezier(p0, p1, p2, n=24):
    """Points along a quadratic curve."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / n for i in range(n + 1))]


def taper(points, w0, w1=None, bulge=0.0):
    """A ribbon along a path, w0 wide at the start and w1 at the end; with
    bulge it swells in the middle (a leaf, a frond)."""
    w1 = w0 if w1 is None else w1
    left, right = [], []
    n = len(points) - 1
    for i, (x, y) in enumerate(points):
        a, b = points[max(0, i - 1)], points[min(n, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        t = i / n
        w = (w0 + (w1 - w0) * t + bulge * math.sin(math.pi * t)) / 2
        left.append((x - dy / d * w, y + dx / d * w))
        right.append((x + dy / d * w, y - dx / d * w))
    return poly(left + right[::-1])


def rrect(x0, y0, x1, y1, r):
    """A rectangle with rounded corners."""
    return union(rect(x0 + r, y0, x1 - r, y1), rect(x0, y0 + r, x1, y1 - r),
                 circle(x0 + r, y0 + r, r), circle(x1 - r, y0 + r, r),
                 circle(x0 + r, y1 - r, r), circle(x1 - r, y1 - r, r))


def ring(cx, cy, r0, r1, y_max=INF):
    """The band between two circles (an arc of it, above y_max)."""
    return Shape(lambda x, y: r0 * r0 <= (x - cx) ** 2 + (y - cy) ** 2 <= r1 * r1
                 and y <= y_max, (cx - r1, cy - r1, cx + r1, min(cy + r1, y_max)))


def polar(cx, cy, radius, rmax):
    """A shape whose edge is radius(angle) from the centre (a leaf, a star,
    a splash); angle 0 points right, going clockwise on screen."""
    def test(x, y):
        dx, dy = x - cx, y - cy
        return math.hypot(dx, dy) <= radius(math.atan2(dy, dx))
    return Shape(test, (cx - rmax, cy - rmax, cx + rmax, cy + rmax))


def star(cx, cy, r_out, r_in, points=5, turn=-90):
    pts = []
    for k in range(points * 2):
        a = math.radians(turn + k * 180 / points)
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


def union(*shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out | s
    return out


# ---------------------------------------------------------------- tone helpers

def noise(x, y, seed=0):
    """Smooth value noise, 0..1."""
    def h(i, j):
        n = (i * 374761393 + j * 668265263 + seed * 2147483647) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return (n & 0xFFFF) / 0xFFFF
    i, j = math.floor(x), math.floor(y)
    fx, fy = x - i, y - j
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    top = h(i, j) + (h(i + 1, j) - h(i, j)) * fx
    bot = h(i, j + 1) + (h(i + 1, j + 1) - h(i, j + 1)) * fx
    return top + (bot - top) * fy


def sphere(cx, cy, r, lx=-0.6, ly=-0.7, lo=0.15, hi=1.0):
    """Tone of a ball lit from (lx, ly): bright towards the light."""
    def tone(x, y):
        dx, dy = (x - cx) / r, (y - cy) / r
        z = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
        lz = math.sqrt(max(0.0, 1 - lx * lx - ly * ly))
        d = max(0.0, dx * lx + dy * ly + z * lz)
        return lo + (hi - lo) * d
    return tone


def grad(x0, y0, x1, y1, lo=0.0, hi=1.0):
    """Tone running from lo at (x0, y0) to hi at (x1, y1)."""
    dx, dy = x1 - x0, y1 - y0
    dd = dx * dx + dy * dy or 1

    def tone(x, y):
        t = ((x - x0) * dx + (y - y0) * dy) / dd
        return lo + (hi - lo) * min(1.0, max(0.0, t))
    return tone


def textured(tone, amount=0.25, scale=12.0, seed=0):
    """A tone with grain mixed in."""
    def t(x, y):
        base = tone(x, y) if callable(tone) else tone
        return min(1.0, max(0.0, base + (noise(x * scale, y * scale, seed) - 0.5) * 2 * amount))
    return t


# ---------------------------------------------------------------- scene parts

class Mat:
    """How a layer looks: ramp is its characters from light to dense, parts
    its colour (a letter, or [(from tone, letter), ...]), edges whether its
    outline uses shaped glyphs, dither whether tone is shown as a halftone."""

    def __init__(self, ramp=" .:-=+*#%@", parts="a", edges=True, dither=False,
                 outline=None, bold=False, code=None, code_below=0.0, code_gap=2, seed=0):
        self.ramp, self.edges, self.dither, self.bold = ramp, edges, dither, bold
        # code: glyphs that fill wherever the tone is under code_below, one
        # every code_gap columns, picked at random (a wall of digits)
        self.code, self.code_below, self.code_gap, self.seed = code, code_below, code_gap, seed
        self.outline = outline          # a colour letter: outline even over other layers
        self.parts = [(0.0, parts)] if isinstance(parts, str) else parts

    def part(self, tone):
        p = self.parts[0][1]
        for t, letter in self.parts:
            if tone >= t:
                p = letter
        return p

    def char(self, tone, r, c):
        if self.code and tone < self.code_below:
            if c % self.code_gap:
                return " "
            n = (r * 7919 + c * 104729 + self.seed * 15485863) & 0xFFFFFFFF
            n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
            return self.code[(n >> 8) % len(self.code)]
        ramp = self.ramp
        if self.dither:
            level = tone * (len(ramp) - 1) + (BAYER[r % 4][c % 4] - 0.5)
            return ramp[min(len(ramp) - 1, max(0, round(level)))]
        return ramp[min(len(ramp) - 1, max(0, int(tone * len(ramp))))]


class Layer:
    def __init__(self, shape, mat, tone=0.7, focus=True):
        self.shape, self.mat, self.focus = shape, mat, focus
        self.tone = tone if callable(tone) else (lambda x, y, t=tone: t)


class Line:
    """A path drawn one character wide, the glyph following its direction
    (or always `char`)."""

    def __init__(self, points, part="a", char=None, focus=True, tone=0.7):
        self.points, self.part, self.char, self.focus = points, part, char, focus
        self.tone = tone


class Stamp:
    """Exact text at a point: stars, sparkles, letters. part is one colour
    letter, or one per character; blanks in text leave what's under them."""

    def __init__(self, x, y, text, part="a", focus=True, tone=0.75):
        self.x, self.y, self.text, self.part, self.focus = x, y, text, part, focus
        self.tone = tone

    def part_at(self, k):
        """The colour of character k; a short colour string carries its
        last letter on."""
        return self.part[min(k, len(self.part) - 1)]


def text(x, y, lines, parts=None, rows=None, focus=True):
    """Several stamps, one under the other: lines of text and their colour
    letters (a letter, or a string per line). rows is the scene's height
    in rows, so each line lands on the next row."""
    out = []
    for k, line in enumerate(lines):
        p = parts[k] if isinstance(parts, (list, tuple)) else (parts or "a")
        out.append(Stamp(x, (int(y * rows) + k + 0.5) / rows, line, p, focus))
    return out


def feather(base, tip, droop, leaf, part="g", every=0.025, sweep=0.6, focus=True):
    """A palm frond or fern: a rib from base to tip with leaflets on both
    sides, `leaf` long, swept back towards the base."""
    mid = ((base[0] + tip[0]) / 2, min(base[1], tip[1]) - droop)
    rib = bezier(base, mid, tip, 48)
    out = [Line(rib, part, focus=focus)]
    length = sum(math.dist(a, b) for a, b in zip(rib, rib[1:]))
    n = max(2, int(length / every))
    for k in range(1, n):
        i = int(k / n * (len(rib) - 1))
        (x0, y0), (x1, y1) = rib[max(0, i - 1)], rib[min(len(rib) - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy) or 1
        dx, dy = dx / d, dy / d
        size = leaf * math.sin(math.pi * (0.15 + 0.85 * k / n))
        x, y = rib[i]
        for side in (1, -1):
            nx, ny = -dy * side, dx * side
            ex = x + (nx - dx * sweep) * size
            ey = y + (ny - dy * sweep) * size + size * 0.4
            out.append(Line([(x, y), (ex, ey)], part, focus=focus))
    return out


def scatter(x0, y0, x1, y1, n, chars, part, seed=1, focus=False):
    """n stamps strewn over a box, one of `chars` each."""
    out = []
    for i in range(n):
        u = noise(i * 7.31 + 0.5, seed * 3.7 + 0.5, seed)
        v = noise(seed * 5.1 + 0.5, i * 9.13 + 0.5, seed + 1)
        u = (u * 7.0) % 1.0
        v = (v * 5.0) % 1.0
        out.append(Stamp(x0 + (x1 - x0) * u, y0 + (y1 - y0) * v,
                         chars[i % len(chars)], part, focus))
    return out


class Scene:
    """aspect is the box's width (its height is 1), or a function giving
    it for a height in rows; parts its layers, lines and stamps, bottom
    first, or a function giving them for a height (for text that can't
    scale); sizes the heights it's made at."""

    def __init__(self, aspect, parts, span=False, sizes=(26, 20, 14, 10)):
        self.span, self.sizes = span, sizes
        self.aspect_of = aspect if callable(aspect) else (lambda rows: aspect)
        self.parts_of = parts if callable(parts) else (lambda rows: parts)


# ---------------------------------------------------------------- rendering

def _glyph_of(dx, dy):
    """A line character for a direction (y grows downwards); dx is in
    screen columns' worth, so the slope is judged as it looks."""
    ang = math.degrees(math.atan2(-dy, dx)) % 180
    if ang < 22 or ang >= 158:
        return "-"
    if ang < 68:
        return "/"
    if ang < 112:
        return "|"
    return "\\"


class _Grid:
    """A scene sampled at some height: which layer covers each of the 4x4
    samples in every cell, and where cells are in scene coordinates."""

    def __init__(self, scene, rows):
        self.rows = rows
        self.unit = unit = 1.0 / rows             # a cell is unit tall, unit/2 wide
        self.cw = cw = unit / 2
        aspect = scene.aspect_of(rows)
        box_cols = max(1, round(aspect / cw))
        self.cols = cols = max(box_cols, SPAN_COLS) if scene.span else box_cols
        self.x_left = x_left = aspect - cols * cw
        self.items = scene.parts_of(rows)
        self.layers = [p for p in self.items if isinstance(p, Layer)]
        self.order = {id(p): z for z, p in enumerate(self.items)}
        self.owner = owner = [None] * (rows * cols)   # per cell: SUB*SUB layer ids
        for li, layer in enumerate(self.layers):
            x0, y0, x1, y1 = layer.shape.box
            c0 = max(0, int((x0 - x_left) / cw) - 1)
            c1 = min(cols, int((x1 - x_left) / cw) + 2)
            r0, r1 = max(0, int(y0 / unit) - 1), min(rows, int(y1 / unit) + 2)
            test = layer.shape.test
            for r in range(r0, r1):
                for c in range(c0, c1):
                    cell = owner[r * cols + c]
                    for j in range(SUB):
                        y = (r + (j + 0.5) / SUB) * unit
                        for i in range(SUB):
                            x = x_left + (c + (i + 0.5) / SUB) * cw
                            if test(x, y):
                                if cell is None:
                                    cell = owner[r * cols + c] = [None] * (SUB * SUB)
                                cell[j * SUB + i] = li

    def at(self, c, r, fx=0.5, fy=0.5):
        """Scene coordinates of a point in cell (c, r)."""
        return self.x_left + (c + fx) * self.cw, (r + fy) * self.unit


def _digit(t):
    return str(min(9, max(0, int(t * 10))))


def _trim(scene, grids, focus):
    """Drop empty rows on top and empty columns on the right (and the
    left, unless the scene spans) from equal-sized grids of strings; the
    first grid holds the characters. Returns the trimmed grids and keep."""
    lines = grids[0]
    top = 0
    while top < len(lines) and not "".join(lines[top]).strip():
        top += 1
    grids = [[row for row in g[top:]] for g in grids]
    focus = focus[top:]
    lines = grids[0]
    cols = len(lines[0]) if lines else 0
    used = [c for c in range(cols) if any(l[c] != " " for l in lines)]
    right = max(used) + 1 if used else 0
    left = 0 if scene.span else (min(used) if used else 0)
    out = [tuple("".join(row[left:right]) for row in g) for g in grids]
    focus = [f[left:right] for f in focus]
    width = right - left
    keep = tuple(next((c for c in range(width) if f[c]), width) for f in focus)
    return out, keep


def render(scene, rows):
    """The scene `rows` tall in ASCII: (lines, parts, tones, keep). tones
    has a digit 0-9 for how light each character is; keep[r] is the first
    column in row r that belongs to the focus (len(line) if none)."""
    g = _Grid(scene, rows)
    cols, layers, order, owner = g.cols, g.layers, g.order, g.owner
    chars = [[" "] * cols for _ in range(rows)]
    parts = [[" "] * cols for _ in range(rows)]
    tones = [[" "] * cols for _ in range(rows)]
    focus = [[False] * cols for _ in range(rows)]
    zof = [[-1] * cols for _ in range(rows)]
    n = SUB * SUB
    for r in range(rows):
        for c in range(cols):
            cell = owner[r * cols + c]
            if not cell:
                continue
            hits = [s for s in cell if s is not None]
            if len(hits) < 2:
                continue
            dom = max(set(hits), key=hits.count)
            layer = layers[dom]
            tone = layer.tone(*g.at(c, r))
            mat = layer.mat
            own = hits.count(dom)
            part = mat.part(tone)
            if mat.outline and n - 2 > own >= 3 and (mat.bold or own < n * 0.6):
                # its own edge, whatever is behind it
                ch = best_glyph([1.0 if s == dom else 0.0 for s in cell], mat.bold)
                part = mat.outline
            elif len(hits) >= n - 2 or not mat.edges:
                t = tone if len(hits) >= n - 2 else tone * len(hits) / n
                ch = mat.char(t, r, c)
            elif len(hits) >= n * 0.6 and not mat.bold:
                ch = mat.char(tone * 0.85, r, c)   # mostly covered: just shade it
            else:
                ch = best_glyph([0.0 if s is None else 1.0 for s in cell], mat.bold)
            if ch == " ":
                continue
            chars[r][c], parts[r][c], tones[r][c] = ch, part, _digit(tone)
            focus[r][c], zof[r][c] = layer.focus, order[id(layer)]

    for p in g.items:
        z = order[id(p)]
        if isinstance(p, Line):
            pts = [((x - g.x_left) / g.cw, y / g.unit) for x, y in p.points]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                steps = max(1, int(max(abs(bx - ax), abs(by - ay)) * 3))
                ch = p.char or _glyph_of((bx - ax) / 2, by - ay)
                for st in range(steps + 1):
                    t = st / steps
                    c, r = int(ax + (bx - ax) * t), int(ay + (by - ay) * t)
                    if 0 <= r < rows and 0 <= c < cols and z > zof[r][c]:
                        chars[r][c], parts[r][c], tones[r][c] = ch, p.part, _digit(p.tone)
                        focus[r][c], zof[r][c] = p.focus, z
        elif isinstance(p, Stamp):
            c0, r = int((p.x - g.x_left) / g.cw), int(p.y / g.unit)
            for k, ch in enumerate(p.text):
                c = c0 + k
                if 0 <= r < rows and 0 <= c < cols and ch != " " and z > zof[r][c]:
                    chars[r][c], parts[r][c] = ch, p.part_at(k).strip() or "a"
                    tones[r][c] = _digit(p.tone)
                    focus[r][c], zof[r][c] = p.focus, z

    (lines, pparts, ptones), keep = _trim(scene, [chars, parts, tones], focus)
    return lines, pparts, ptones, keep


# a cell's four quadrants (top-left, top-right, bottom-left, bottom-right)
# drawn in the foreground colour, as a block character
QUADRANTS = {
    (0, 0, 0, 0): " ", (1, 0, 0, 0): "▘", (0, 1, 0, 0): "▝", (0, 0, 1, 0): "▖",
    (0, 0, 0, 1): "▗", (1, 1, 0, 0): "▀", (0, 0, 1, 1): "▄", (1, 0, 1, 0): "▌",
    (0, 1, 0, 1): "▐", (1, 0, 0, 1): "▚", (0, 1, 1, 0): "▞", (1, 1, 1, 0): "▛",
    (1, 1, 0, 1): "▜", (1, 0, 1, 1): "▙", (0, 1, 1, 1): "▟", (1, 1, 1, 1): "█",
}


# braille: each cell is 2 dots across and 4 down; the bit for each dot
BRAILLE_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))
# text that's really a line, and which dot rows it fills
STREAKS = {"=": (1, 2), "-": (2,), "~": (1, 2), "_": (3,)}


def _closeness(a, b):
    """How unlike two (part, tone) colours are: another part is far."""
    return (a[0] != b[0]) * 10 + abs(int(a[1]) - int(b[1]))


def render_blocks(scene, rows):
    """The scene `rows` tall in block characters: each cell is four
    quadrants, each its own colour, drawn as a quadrant or half block in
    one colour on a background of another. Fine detail is braille, 2x4
    dots a cell: lines, line-like text (= - ~ _) and dithered textures,
    over whatever colour is behind. Other text (stamps, code glyphs)
    stays text, on the colour behind it. Returns (lines, parts, tones,
    back_parts, back_tones, keep); a blank back part means the terminal's
    own background."""
    g = _Grid(scene, rows)
    cols, layers, order, owner = g.cols, g.layers, g.order, g.owner
    qr, qc = rows * 2, cols * 2
    quad = [[None] * qc for _ in range(qr)]       # (part, tone digit)
    qz = [[-1] * qc for _ in range(qr)]
    qfocus = [[False] * qc for _ in range(qr)]
    text = {}                                     # (r, c): (char, part, tone, focus, z)
    dots = {}                                     # (dot row, dot col): (colour, z, focus)

    def dot(R, C, colour, z, foc):
        if 0 <= R < rows * 4 and 0 <= C < cols * 2:
            old = dots.get((R, C))
            if old is None or z > old[1]:
                dots[(R, C)] = (colour, z, foc)
    h = SUB // 2
    for r in range(rows):
        for c in range(cols):
            cell = owner[r * cols + c]
            if not cell:
                continue
            for qy in (0, 1):
                for qx in (0, 1):
                    ids = [cell[(qy * h + j) * SUB + qx * h + i] for j in range(h) for i in range(h)]
                    hits = [s for s in ids if s is not None]
                    if len(hits) < 2:
                        continue
                    layer = layers[max(set(hits), key=hits.count)]
                    mat = layer.mat
                    tone = layer.tone(*g.at(c, r, (qx + 0.5) / 2, (qy + 0.5) / 2))
                    z = order[id(layer)]
                    if mat.code and tone < mat.code_below:
                        # a wall of glyphs stays text
                        ch = mat.char(tone, r, c)
                        if ch != " " and (r, c) not in text:
                            text[(r, c)] = (ch, mat.part(tone), _digit(tone), layer.focus, z)
                        continue
                    if mat.dither:
                        # a sparse texture: braille dots, each by its own tone
                        for dy in (0, 1):
                            for dx in (0, 1):
                                Rd, Cd = r * 4 + qy * 2 + dy, c * 2 + qx
                                t = layer.tone(*g.at(c, r, (qx + 0.5) / 2, (qy * 2 + dy + 0.5) / 4))
                                if t > BAYER[Rd % 4][(Cd + dx * 2) % 4] * 1.4:
                                    dot(Rd, Cd, (mat.part(t), _digit(t)), z, layer.focus)
                        continue
                    elif tone <= 0.0:
                        continue                 # a deliberate gap (stripes, ripples)
                    R, C = r * 2 + qy, c * 2 + qx
                    quad[R][C], qz[R][C], qfocus[R][C] = (mat.part(tone), _digit(tone)), z, layer.focus

    for p in g.items:
        z = order[id(p)]
        if isinstance(p, Line):
            # one braille dot wide
            pts = [((x - g.x_left) / g.cw * 2, y / g.unit * 4) for x, y in p.points]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                steps = max(1, int(max(abs(bx - ax), abs(by - ay)) * 2))
                for st in range(steps + 1):
                    t = st / steps
                    dot(int(ay + (by - ay) * t), int(ax + (bx - ax) * t),
                        (p.part, _digit(p.tone)), z, p.focus)
        elif isinstance(p, Stamp):
            c0, r = int((p.x - g.x_left) / g.cw), int(p.y / g.unit)
            for k, ch in enumerate(p.text):
                c = c0 + k
                if ch in STREAKS:
                    colour = (p.part_at(k).strip() or "a", _digit(p.tone))
                    for dy in STREAKS[ch]:
                        for dx in (0, 1):
                            dot(r * 4 + dy, c * 2 + dx, colour, z, p.focus)
                    continue
                if 0 <= r < rows and 0 <= c < cols and ch != " ":
                    old = text.get((r, c))
                    if old is None or z > old[4]:
                        text[(r, c)] = (ch, p.part_at(k).strip() or "a", _digit(p.tone), p.focus, z)

    grids = [[[" "] * cols for _ in range(rows)] for _ in range(5)]
    chars, parts, tones, bparts, btones = grids
    focus = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            cells = [(r * 2, c * 2), (r * 2, c * 2 + 1), (r * 2 + 1, c * 2), (r * 2 + 1, c * 2 + 1)]
            cols4 = [quad[R][C] for R, C in cells]
            zs = [qz[R][C] for R, C in cells]
            focus[r][c] = any(qfocus[R][C] for R, C in cells)
            t = text.get((r, c))
            if t and t[4] >= max(zs):
                # text on top of whatever is mostly behind it
                ch, part, tone, foc, _ = t
                filled = [x for x in cols4 if x]
                back = max(set(filled), key=filled.count) if len(filled) >= 2 else None
                chars[r][c], parts[r][c], tones[r][c] = ch, part, tone
                if back:
                    bparts[r][c], btones[r][c] = back
                focus[r][c] = focus[r][c] or foc
                continue
            cell_dots = [(dy, dx, dots[(r * 4 + dy, c * 2 + dx)]) for dy in range(4) for dx in (0, 1)
                         if (r * 4 + dy, c * 2 + dx) in dots]
            cell_dots = [(dy, dx, d) for dy, dx, d in cell_dots if d[1] > max(zs)]
            if cell_dots:
                # braille dots over the colour behind them
                bits, colours = 0, []
                for dy, dx, (colour, z, foc) in cell_dots:
                    bits |= BRAILLE_BITS[dy][dx]
                    colours.append(colour)
                    focus[r][c] = focus[r][c] or foc
                fg = max(set(colours), key=colours.count)
                filled = [x for x in cols4 if x]
                back = max(set(filled), key=filled.count) if len(filled) >= 2 else None
                chars[r][c] = chr(0x2800 + bits)
                parts[r][c], tones[r][c] = fg
                if back:
                    bparts[r][c], btones[r][c] = back
                continue
            if not any(cols4):
                continue
            # the two colours that matter most; the rest join the nearer one
            counts = {}
            for x in cols4:
                counts[x] = counts.get(x, 0) + 1
            top2 = sorted(counts, key=lambda x: (-counts[x], x is None))[:2]
            mapped = []
            for x in cols4:
                if x in top2:
                    mapped.append(x)
                elif x is None:
                    mapped.append(None if None in top2 else min(top2, key=lambda y: int(y[1])))
                else:
                    near = [y for y in top2 if y is not None]
                    mapped.append(min(near, key=lambda y: _closeness(x, y)))
            kinds = list(dict.fromkeys(mapped))
            if len(kinds) == 1:
                fg, bg = kinds[0], None
            elif None in kinds:
                fg, bg = [k for k in kinds if k is not None][0], None
            else:
                # the nearer layer in front
                za = max(z for z, x in zip(zs, cols4) if x == kinds[0]) if kinds[0] in cols4 else -1
                zb = max(z for z, x in zip(zs, cols4) if x == kinds[1]) if kinds[1] in cols4 else -1
                fg, bg = (kinds[0], kinds[1]) if za >= zb else (kinds[1], kinds[0])
            mask = tuple(1 if x == fg else 0 for x in mapped)
            chars[r][c] = QUADRANTS[mask]
            parts[r][c], tones[r][c] = fg
            if bg is not None and mask != (1, 1, 1, 1):
                bparts[r][c], btones[r][c] = bg

    (lines, pparts, ptones, pb, tb), keep = _trim(scene, [chars, parts, tones, bparts, btones], focus)
    return lines, pparts, ptones, pb, tb, keep
