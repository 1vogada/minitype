"""The "combined" art style: pictures drawn with every technique at once,
for tools/make_art.py.

A combined scene is a colour field rather than shapes: field(x, y) gives
the colour at any point (with how opaque it is, whether it's focus, and
what it is), in the same coordinates as artgen (y 0 at the top to 1 at
the bottom, x to the scene's aspect, cells half as wide as tall). On top
of that come fine lines and text.

Every cell is sampled 4 across and 8 down, and drawn as whichever of
these comes closest to the samples, in the theme's real colours:

    a solid colour                       █
    two colours mixed in a shade         ░ ▒ ▓  (smooth gradients)
    an edge between two colours          quadrants ▘▝▖▗▚▞▙▛▜▟▀▄▌▐,
                                         eighths ▁▂▃▅▆▇▔ and ▎▊▕
                                         (crisp horizons and stripes)
    fine lines, one dot wide             braille, over the colour behind
    text                                 stars, sparkle, reflections

The result is stored like the blocks pictures: a character, its colour
and its background colour for every cell.
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

SPAN_COLS = 160
SX, SY = 4, 8                    # samples per cell, across and down
N = SX * SY

# ---------------------------------------------------------------- glyph masks

def _mask(test):
    return tuple(i for i in range(N) if test(i % SX, i // SX))


MASKS = []                       # (character, sample indices drawn in the foreground)
_QUADS = {"▘": (1, 0, 0, 0), "▝": (0, 1, 0, 0), "▖": (0, 0, 1, 0), "▗": (0, 0, 0, 1),
          "▀": (1, 1, 0, 0), "▄": (0, 0, 1, 1), "▌": (1, 0, 1, 0), "▐": (0, 1, 0, 1),
          "▚": (1, 0, 0, 1), "▞": (0, 1, 1, 0), "▛": (1, 1, 1, 0), "▜": (1, 1, 0, 1),
          "▙": (1, 0, 1, 1), "▟": (0, 1, 1, 1)}
for ch, q in _QUADS.items():
    MASKS.append((ch, _mask(lambda x, y, q=q: q[(y >= SY // 2) * 2 + (x >= SX // 2)])))
for k, ch in enumerate("▁▂▃▅▆▇", 1):
    k = k if k < 4 else k + 1                     # ▄ is a quadrant mask already
    MASKS.append((ch, _mask(lambda x, y, k=k: y >= SY - k)))
MASKS.append(("▔", _mask(lambda x, y: y == 0)))
MASKS.append(("▎", _mask(lambda x, y: x == 0)))
MASKS.append(("▊", _mask(lambda x, y: x <= 2)))
MASKS.append(("▕", _mask(lambda x, y: x == SX - 1)))
SHADES = ((0.25, "░"), (0.5, "▒"), (0.75, "▓"))
SHADE_COST = 250                 # shades read grainy: a mix must beat a solid by this
EDGE_COST = 20

# braille: 2 dots across, 4 down
BRAILLE_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))


# ---------------------------------------------------------------- colour

def dist(a, b):
    """How unlike two colours look (weighted for the eye)."""
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return 2 * dr * dr + 4 * dg * dg + 3 * db * db


def mix(a, b, t):
    """a to b, t of the way."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def ramp(stops, t):
    """A colour along stops [(t, colour), ...]."""
    t = min(max(t, stops[0][0]), stops[-1][0])
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return mix(c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0)
    return stops[-1][1]


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class Palette:
    """The theme's art colours, (letter, tone) -> rgb, plus the ground
    (key None): the background under the art."""

    def __init__(self, theme):
        os.environ.setdefault("COLORTERM", "truecolor")
        from minitype.terminal import style
        st = style.Styles(theme)
        pal = st.art_palette(True)
        letters = dict(zip(("dim", "text", "error", "extra", "accent", "good", "warn"), "dtexagw"))
        self.colours = []
        for part, letter in letters.items():
            for t in range(10):
                rgb = style.rgb_of_code(pal[(part, str(t))])
                if rgb:
                    self.colours.append(((letter, str(t)), rgb))
        self.ground = style.rgb_of_code(st.background, 48) or (18, 18, 22)
        self.all = self.colours + [(None, self.ground)]
        self._near = {}
        self._by_key = dict(self.colours)

    def rgb(self, key):
        """A colour by its short name: "e6" is error, tone 6; "-" the ground."""
        return self.ground if key == "-" else self._by_key[(key[0], key[1])]

    def path(self, keys):
        """A gradient, t 0 to 1, that runs from one palette colour to the
        next ("a0 a1 x2 -"). Every point on it is between two colours the
        theme has, so it's drawn exactly by them and the shades between."""
        stops = [self.rgb(k) for k in keys.split()]
        n = len(stops) - 1

        def at(t):
            t = min(1.0, max(0.0, t)) * n
            i = min(int(t), n - 1)
            return mix(stops[i], stops[i + 1], t - i)
        return at

    def nearest(self, c, k=1, ground=True):
        """The k palette entries closest to c, nearest first."""
        key = (int(c[0]) >> 2, int(c[1]) >> 2, int(c[2]) >> 2, k, ground)
        hit = self._near.get(key)
        if hit is None:
            pool = self.all if ground else self.colours
            hit = sorted(pool, key=lambda e: dist(c, e[1]))[:k]
            self._near[key] = hit
        return hit


# ---------------------------------------------------------------- the scene

class Scene:
    """field(x, y) -> (rgb, alpha, focus, tag); lines(rows) -> [(points,
    rgb or fn(x, y), focus, hidden(x, y) or None)]; texts(rows, x_left,
    cw, unit) -> [(col, row, char, rgb, focus)]."""

    def __init__(self, aspect, field, lines=None, texts=None, span=True,
                 sizes=(26, 20, 14, 10), theme="default"):
        self.aspect, self.field, self.span, self.sizes, self.theme = aspect, field, span, sizes, theme
        self.lines = lines or (lambda rows: [])
        self.texts = texts or (lambda rows, x_left, cw, unit: [])


def render(scene, rows, pal=None):
    """The scene `rows` tall: (lines, parts, tones, back_parts, back_tones,
    keep), like artgen.render_blocks."""
    pal = pal or Palette(scene.theme)
    unit = 1.0 / rows
    cw = unit / 2
    box = max(1, round(scene.aspect / cw))
    cols = max(box, SPAN_COLS) if scene.span else box
    x_left = scene.aspect - cols * cw
    ground = pal.ground

    # the field, sampled
    cells = {}                        # (r, c) -> (samples, focus, tags, mean)
    for r in range(rows):
        for c in range(cols):
            samples, focus, tags, seen = [], False, {}, False
            for j in range(SY):
                y = (r + (j + 0.5) / SY) * unit
                for i in range(SX):
                    x = x_left + (c + (i + 0.5) / SX) * cw
                    rgb, a, foc, tag = scene.field(x, y)
                    if a > 0:
                        seen = True
                        focus = focus or foc
                        tags[tag] = tags.get(tag, 0) + 1
                        samples.append(mix(ground, rgb, a) if a < 1 else rgb)
                    else:
                        samples.append(ground)
            if seen:
                n = len(samples)
                mean = (sum(s[0] for s in samples) / n, sum(s[1] for s in samples) / n,
                        sum(s[2] for s in samples) / n)
                cells[(r, c)] = (samples, focus, tags, mean)

    # fine lines, as braille dots
    dots = {}                         # (dot row, dot col) -> (rgb, focus)
    for points, colour, foc, hidden in scene.lines(rows):
        pts = [((x - x_left) / cw * 2, y / unit * 4) for x, y in points]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            steps = max(1, int(max(abs(bx - ax), abs(by - ay)) * 2))
            for st in range(steps + 1):
                t = st / steps
                R, C = int(ay + (by - ay) * t), int(ax + (bx - ax) * t)
                if not (0 <= R < rows * 4 and 0 <= C < cols * 2):
                    continue
                x, y = x_left + (C + 0.5) / 2 * cw, (R + 0.5) / 4 * unit
                if hidden and hidden(x, y):
                    continue
                dots[(R, C)] = (colour(x, y) if callable(colour) else colour, foc)

    texts = {(r, c): (ch, rgb, foc) for c, r, ch, rgb, foc in scene.texts(rows, x_left, cw, unit)
             if 0 <= r < rows and 0 <= c < cols}

    chars = [[" "] * cols for _ in range(rows)]
    parts = [[" "] * cols for _ in range(rows)]
    tones = [[" "] * cols for _ in range(rows)]
    bparts = [[" "] * cols for _ in range(rows)]
    btones = [[" "] * cols for _ in range(rows)]
    focus = [[False] * cols for _ in range(rows)]

    def put(r, c, ch, fg, bg):
        chars[r][c] = ch
        if fg is not None:
            parts[r][c], tones[r][c] = fg
        if bg is not None:
            bparts[r][c], btones[r][c] = bg

    for r in range(rows):
        for c in range(cols):
            cell = cells.get((r, c))
            mean = cell[3] if cell else ground
            if cell:
                focus[r][c] = cell[1]
            back = pal.nearest(mean)[0][0] if cell else None
            text = texts.get((r, c))
            if text:
                ch, rgb, foc = text
                put(r, c, ch, pal.nearest(rgb, ground=False)[0][0], back)
                focus[r][c] = focus[r][c] or foc
                continue
            cell_dots = [(dy, dx, dots[(r * 4 + dy, c * 2 + dx)]) for dy in range(4) for dx in (0, 1)
                         if (r * 4 + dy, c * 2 + dx) in dots]
            if cell_dots:
                bits = 0
                for dy, dx, (rgb, foc) in cell_dots:
                    bits |= BRAILLE_BITS[dy][dx]
                    focus[r][c] = focus[r][c] or foc
                n = len(cell_dots)
                avg = tuple(sum(d[2][0][k] for d in cell_dots) / n for k in range(3))
                put(r, c, chr(0x2800 + bits), pal.nearest(avg, ground=False)[0][0], back)
                continue
            if not cell:
                continue
            ch, fg, bg = encode(cell[0], mean, pal, shades=max(cell[2], key=cell[2].get) != "floor")
            if ch != " " or bg is not None:
                put(r, c, ch, fg, bg)

    return _trim(scene, chars, parts, tones, bparts, btones, focus)


def encode(samples, mean, pal, shades=True):
    """The character, foreground and background (palette keys; None for
    the ground) that best draw these samples."""
    n = len(samples)
    var = sum(dist(s, mean) for s in samples)
    best = None

    def consider(err, ch, fg, bg):
        nonlocal best
        if best is None or err < best[0]:
            best = (err, ch, fg, bg)

    # one colour, or two mixed in a shade
    near = pal.nearest(mean, 6)
    for key, rgb in near:
        consider(var + n * dist(mean, rgb), " " if key is None else "█", key, None)
    for i, (fk, frgb) in enumerate(near if shades else ()):
        if fk is None:
            continue
        for bk, brgb in near:
            if bk == fk:
                continue
            for a, ch in SHADES:
                # shades read a little grainy: only worth it when they're closer
                err = var + n * dist(mean, mix(brgb, frgb, a)) + n * SHADE_COST
                consider(err, ch, fk, bk)
    # an edge: worth trying only if the samples aren't all alike
    if var > n * 150:
        for ch, mask in MASKS:
            inside = set(mask)
            a = [samples[i] for i in mask]
            b = [samples[i] for i in range(n) if i not in inside]
            ma = tuple(sum(s[k] for s in a) / len(a) for k in range(3))
            mb = tuple(sum(s[k] for s in b) / len(b) for k in range(3))
            fk, frgb = pal.nearest(ma, ground=False)[0]
            bk, brgb = pal.nearest(mb)[0]
            err = sum(dist(s, frgb) for s in a) + sum(dist(s, brgb) for s in b) + n * EDGE_COST
            consider(err, ch, fk, bk)
    _, ch, fg, bg = best
    return ch, fg, bg


def _trim(scene, chars, parts, tones, bparts, btones, focus):
    """Drop empty rows on top and empty columns on the right (and left,
    unless the scene spans); join rows into strings. keep[r] is the first
    focus column of row r (the width if none)."""
    rows = len(chars)
    filled = lambda r: any(ch != " " or bparts[r][c] != " " for c, ch in enumerate(chars[r]))
    top = 0
    while top < rows and not filled(top):
        top += 1
    cols = len(chars[0])
    used = [c for c in range(cols) if any(chars[r][c] != " " or bparts[r][c] != " "
                                          for r in range(top, rows))]
    right = max(used) + 1 if used else 0
    left = 0 if scene.span else (min(used) if used else 0)
    out = [tuple("".join(g[r][left:right]) for r in range(top, rows))
           for g in (chars, parts, tones, bparts, btones)]
    width = right - left
    keep = tuple(next((c for c in range(width) if focus[r][left + c]), width)
                 for r in range(top, rows))
    return (*out, keep)


# ---------------------------------------------------------------- vaporwave
def vaporwave(pal):
    """A vaporwave sunset: a sky from indigo through violet to magenta that
    dissolves into the background at its edges, stars, a big striped sun
    from cream to hot pink with a glow, wireframe mountains on the
    horizon, two palm silhouettes rim-lit in pink with feathered fronds,
    and a neon grid floor with the sun's reflection, running across the
    whole bottom of the screen. Every gradient runs along the theme's own
    colours (see Palette.path), so it shades smoothly with no blotches."""
    hz = 0.64                                   # the horizon
    sun_x, sun_y, sun_r = 0.95, 0.39, 0.25
    sky = pal.path("a0 a1 x1 x2 x3 e3 e4 x5")    # top to horizon
    sun = pal.path("w9 w7 w6 e7 e6 e5")
    floor = pal.path("e4 x2 x1 -")                # horizon to the bottom
    mount = pal.path("x3 x2 x1 -")
    rim = pal.rgb("e6")
    dark = pal.ground

    def ridge(x):
        """The mountains' top edge (smaller y is higher)."""
        h = 0.0
        for cx, w, ht in ((0.3, 0.2, 0.14), (0.5, 0.12, 0.09), (0.12, 0.13, 0.07),
                          (1.36, 0.16, 0.11), (1.52, 0.12, 0.08), (0.7, 0.08, 0.035)):
            h = max(h, ht * max(0.0, 1 - abs(x - cx) / w) ** 1.15)
        return hz - h

    def curve(p0, p1, p2, n=24):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
                for t in (k / n for k in range(n + 1))]

    # the palms: trunk and fronds as polylines with a width along them
    strokes = []                                # (points, width(t), kind, scale)
    palms = (((1.36, 1.03), (1.4, 0.66), (1.3, 0.3), 0.9),
             ((0.36, 1.03), (0.33, 0.8), (0.45, 0.52), 0.6))
    for base, bend, crown, s in palms:
        strokes.append((curve(base, bend, crown), lambda t, s=s: (0.034 - 0.014 * t) * s, "trunk", s))
        # each frond arches up out of the crown and droops to its tip; the
        # angle is the way it sets off (0 right, 90 straight up)
        for ang, ln, droop in ((166, 0.4, 0.26), (132, 0.28, 0.1), (92, 0.2, 0.03),
                               (48, 0.3, 0.12), (12, 0.38, 0.27), (200, 0.24, 0.2)):
            a = math.radians(ang)
            ln *= s
            dx, dy = math.cos(a), -math.sin(a) * 0.75
            mid = (crown[0] + dx * ln * 0.5, crown[1] + dy * ln * 0.5 - 0.07 * s)
            tip = (crown[0] + dx * ln, crown[1] + dy * ln + droop * s)
            strokes.append((curve(crown, mid, tip),
                            lambda t, s=s: (0.004 + 0.024 * math.sin(math.pi * min(1.0, 0.15 + t)) ** 0.8) * s,
                            "frond", s))
    segs = []                                   # (ax, ay, bx, by, t0, t1, length so far, stroke)
    for si, (pts, width, kind, _) in enumerate(strokes):
        run = 0.0
        for k, (a, b) in enumerate(zip(pts, pts[1:])):
            n = len(pts) - 1
            segs.append((a[0], a[1], b[0], b[1], k / n, (k + 1) / n, run, si))
            run += math.hypot(b[0] - a[0], b[1] - a[1])
    reach = 0.09
    boxes = [(min(g[0], g[2]) - reach, min(g[1], g[3]) - reach,
              max(g[0], g[2]) + reach, max(g[1], g[3]) + reach) for g in segs]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
           max(b[2] for b in boxes), max(b[3] for b in boxes))

    def palm_at(x, y):
        """"trunk", "frond" or None at (x, y)."""
        if not (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
            return None
        for (ax, ay, bx, by, t0, t1, run, si), (x0, y0, x1, y1) in zip(segs, boxes):
            if not (x0 <= x <= x1 and y0 <= y <= y1):
                continue
            dx, dy = bx - ax, by - ay
            ll = dx * dx + dy * dy or 1e-9
            u = min(1.0, max(0.0, ((x - ax) * dx + (y - ay) * dy) / ll))
            px, py = ax + dx * u, ay + dy * u
            d = math.hypot(x - px, y - py)
            pts, width, kind, scale = strokes[si]
            t = t0 + (t1 - t0) * u
            w = width(t)
            if d <= w:
                return kind
            if kind != "frond" or t < 0.18:
                continue
            # leaflets: teeth swept back towards the crown, longer below
            below = (y - py) > 0
            reach_ = (0.038 if below else 0.016) * math.sin(math.pi * min(1.0, t)) ** 0.6 * scale
            if d > w + reach_:
                continue
            along = run + math.sqrt(ll) * u
            if ((along * 30 + (d - w) / max(reach_, 1e-6) * 0.55) % 1.0) < 0.42:
                return kind
        return None

    def sky_at(x, y):
        t = y / hz
        glow = math.exp(-((math.hypot(x - sun_x, y - sun_y) / 0.45) ** 2)) * 0.22
        return sky(min(1.0, t + glow))

    def field(x, y):
        kind = palm_at(x, y)
        if kind:
            c = dark
            if kind == "trunk" and math.sin(y * 240) > 0.55:
                c = pal.rgb("x1")                       # the trunk's rings
            if y < hz + 0.03 and palm_at(x + 0.012, y) is None:
                c = rim                                 # lit from the sun
            return c, 1.0, True, "palm"
        if y >= hz:
            t = (y - hz) / (1 - hz)
            near = math.exp(-((x - sun_x) / 0.55) ** 2)
            return floor(min(1.0, t * (3.2 - 1.4 * near))), 1.0, False, "floor"
        alpha = smooth(-0.08, 0.42, x) * smooth(-0.12, 0.06, y)
        if alpha <= 0.03:
            return None, 0.0, False, None
        top = ridge(x)
        if y >= top:
            return mount((y - top) / max(0.01, hz - top)), max(alpha, 0.99), True, "mount"
        if math.hypot(x - sun_x, y - sun_y) <= sun_r:
            k = (y - (sun_y - sun_r)) / (2 * sun_r)        # 0 at the top, 1 at the bottom
            if not (k > 0.5 and ((k - 0.5) * 11) % 1.0 < 0.16 + 0.6 * (k - 0.5)):
                return sun(k), 1.0, True, "sun"
        return sky_at(x, y), alpha, True, "sky"

    def lines(rows):
        out = []
        hidden = lambda x, y: palm_at(x, y) is not None
        grid = lambda x, y: pal.path("e7 x7 a7 a8")(min(1.0, (y - hz) / (1 - hz) * 1.3))
        out.append(([(-6.0, hz + 0.003), (1.6, hz + 0.003)], pal.rgb("e8"), False, hidden))
        per = rows * 4                            # dots per unit, down
        for k in range(-9, 9):                   # further out only the rows go on
            # each vertical starts where it's 8 dots clear of the next
            t0 = min(0.95, 8 / (0.2 * per * 2))
            y0 = hz + (1 - hz) * t0
            out.append(([(sun_x + k * 0.2 * t0, y0), (sun_x + k * 0.2, 1.0)], grid, False, hidden))
        for t in (0.16, 0.36, 0.62, 0.94):           # closer together further off
            y = hz + (1 - hz) * t
            out.append(([(-6.0, y), (1.6, y)], grid, False, hidden))
        # wireframe mountains: the ridge, and a few lines down each face
        pts = [(x / 300, ridge(x / 300)) for x in range(0, 470)]
        run = []
        for p in pts + [None]:
            if p and p[1] < hz - 0.003:
                run.append(p)
                continue
            if len(run) > 1:
                out.append((run, pal.rgb("e8"), True, hidden))
            run = []
        return out

    def texts(rows, x_left, cw, unit):
        out = []
        rng = random.Random(11)
        for _ in range(int(rows * 4)):
            x, y = rng.uniform(0.1, 1.5), rng.uniform(0.0, hz * 0.5)
            rgb, a, foc, tag = field(x, y)
            if tag != "sky" or a < 0.55 or math.hypot(x - sun_x, y - sun_y) < sun_r + 0.07:
                continue
            ch = rng.choice("..·'+*")
            out.append((int((x - x_left) / cw), int(y / unit), ch,
                        pal.rgb(rng.choice(("t8", "t9", "w9", "a9"))), True))
        # the sun's reflection on the floor: broken streaks under it
        r0 = int(hz / unit) + 1
        for r in range(r0, min(rows, r0 + max(2, rows // 6))):
            y = (r + 0.5) * unit
            t = (y - hz) / (1 - hz)
            half = sun_r * (0.95 - t * 2.2)
            for c in range(int((sun_x - half - x_left) / cw), int((sun_x + half - x_left) / cw) + 1):
                x = x_left + (c + 0.5) * cw
                if palm_at(x, y) or rng.random() < 0.2 + t * 2.5:
                    continue
                ch = "=" if t < 0.07 else "-" if t < 0.16 else "~"
                out.append((c, r, ch, pal.path("w8 e7 e6")(min(1.0, t * 5)), False))
        return out

    return Scene(1.5, field, lines, texts, span=True, theme="vaporwave")


# combined pictures by art name, and the theme each is drawn for
SCENES = {"palm": (vaporwave, "vaporwave")}


if __name__ == "__main__":
    import time
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    make, theme = SCENES[sys.argv[1] if len(sys.argv) > 1 else "palm"]
    pal = Palette(theme)
    rows = int(sys.argv[2]) if len(sys.argv) > 2 else 26
    t = time.time()
    lines = render(make(pal), rows, pal)[0]
    print("\n".join(l[-110:] for l in lines))
    print(f"{time.time() - t:.1f}s")
