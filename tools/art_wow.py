"""Big pictures in every technique at once (tools/art_combined.py's
renderer: shades, eighths, quadrants, braille, text), about 28 rows tall,
for the revamp art style. Each is a colour field in its theme's own
palette; every gradient runs along palette colours (Palette.path) so it
shades smoothly.

Shared pieces: a sky, discs (sun / moon) with sphere shading, ridges,
pine trees, a palm, the sea with a reflection, stars.
"""

import math
import random

from art_combined import Scene, mix

ROWS = 28
SIZES = (28, 22, 16)       # biggest first: smaller windows get a smaller one
SHADE = 60                  # shades cheap: gradients in ░▒▓, as in the vaporwave sky


# ---------------------------------------------------------------- pieces

def ridge(peaks, base):
    """A mountain line: the highest of triangular peaks (x, width, height)
    over base (smaller y is higher)."""
    def top(x):
        h = 0.0
        for cx, w, ht in peaks:
            h = max(h, ht * max(0.0, 1 - abs(x - cx) / w) ** 1.1)
        h += 0.006 * math.sin(x * 90) + 0.004 * math.sin(x * 211)
        return base - max(0.0, h)
    return top


def pine(cx, base, height, width, tiers=5):
    """A pine: stacked triangles narrowing upwards, and a short trunk."""
    def inside(x, y):
        t = (base - y) / height                 # 0 at the base, 1 at the tip
        if t < 0 or t > 1:
            return False
        if t < 0.08:
            return abs(x - cx) < width * 0.08
        k = (t - 0.08) / 0.92
        tier = (k * tiers) % 1.0                # each tier widest at its bottom
        half = width * (1 - k) * (0.55 + 0.45 * (1 - tier))
        return abs(x - cx) <= half
    return inside


def palm(base, crown, scale, lean=0.0):
    """A palm silhouette: a curved trunk and arching fronds; returns
    inside(x, y)."""
    def curve(p0, p1, p2, n=20):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
                for t in (k / n for k in range(n + 1))]
    strokes = [(curve(base, ((base[0] + crown[0]) / 2 + lean, (base[1] + crown[1]) / 2), crown),
                lambda t: (0.022 - 0.009 * t) * scale)]
    for ang, ln, droop in ((166, 0.36, 0.22), (132, 0.26, 0.09), (92, 0.18, 0.02),
                           (50, 0.26, 0.1), (14, 0.36, 0.24), (200, 0.22, 0.18), (-20, 0.2, 0.18)):
        a = math.radians(ang)
        ln *= scale
        dx, dy = math.cos(a), -math.sin(a) * 0.75
        mid = (crown[0] + dx * ln * 0.5, crown[1] + dy * ln * 0.5 - 0.06 * scale)
        tip = (crown[0] + dx * ln, crown[1] + dy * ln + droop * scale)
        strokes.append((curve(crown, mid, tip),
                        lambda t: (0.004 + 0.022 * math.sin(math.pi * min(1.0, 0.12 + t)) ** 0.8) * scale))
    segs = []
    for pts, width in strokes:
        n = len(pts) - 1
        for k, (a, b) in enumerate(zip(pts, pts[1:])):
            segs.append((a, b, width(k / n), width((k + 1) / n)))
    xs = [p[0] for pts, _ in strokes for p in pts]
    ys = [p[1] for pts, _ in strokes for p in pts]
    box = (min(xs) - 0.05, min(ys) - 0.05, max(xs) + 0.05, max(ys) + 0.05)

    def inside(x, y):
        if not (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
            return False
        for (ax, ay), (bx, by), ra, rb in segs:
            dx, dy = bx - ax, by - ay
            ll = dx * dx + dy * dy or 1e-9
            u = min(1.0, max(0.0, ((x - ax) * dx + (y - ay) * dy) / ll))
            if (x - ax - dx * u) ** 2 + (y - ay - dy * u) ** 2 <= (ra + (rb - ra) * u) ** 2:
                return True
        return False
    return inside


def sphere_light(cx, cy, r, lx=-0.55, ly=-0.6):
    """0..1 light on a ball lit from (lx, ly)."""
    lz = math.sqrt(max(0.0, 1 - lx * lx - ly * ly))

    def light(x, y):
        dx, dy = (x - cx) / r, (y - cy) / r
        z = math.sqrt(max(0.0, 1 - dx * dx - dy * dy))
        return max(0.0, dx * lx + dy * ly + z * lz)
    return light


def stars(field, rows, x_left, cw, unit, n, y_max, colours, seed, chars="..·'+*"):
    """Stars as text, only where the field says sky."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rng.uniform(-3.0, 2.0), rng.uniform(0.0, y_max)
        if field(x, y)[3] != "sky":
            continue
        out.append((int((x - x_left) / cw), int(y / unit), rng.choice(chars),
                    rng.choice(colours), field(x, y)[2]))
    return out


# ---------------------------------------------------------------- ocean

def island(pal):
    hz = 0.64
    sun_x, sun_y, sun_r = 0.62, 0.5, 0.1
    sky = pal.path("a1 a4 d6 w4 w6 e6 e7")
    sea = pal.path("e4 a4 a1 -")
    sun = pal.path("w9 w8 w6 e6")
    tree = palm((1.42, 0.97), (1.28, 0.42), 1.0, lean=0.1)
    tree2 = palm((1.67, 0.98), (1.6, 0.56), 0.7, lean=0.06)
    dark = pal.ground

    def cloud(x, y):
        """Long soft clouds above the sun."""
        for cx, cy, w, h in ((0.3, 0.3, 0.45, 0.035), (0.95, 0.24, 0.35, 0.03), (0.55, 0.4, 0.3, 0.02),
                             (-0.6, 0.28, 0.5, 0.03), (-1.6, 0.35, 0.6, 0.03)):
            d = ((x - cx) / w) ** 2 + ((y - cy) / h) ** 2
            if d < 1:
                return 1 - d
        return 0.0

    def field(x, y):
        if tree(x, y) or tree2(x, y):
            c = dark
            if y < hz and not tree(x - 0.012, y) and not tree2(x - 0.012, y):
                c = pal.rgb("e6")                     # rim lit by the sun
            return c, 1.0, True, "palm"
        island_top = 0.9 - 0.06 * math.exp(-((x - 1.5) / 0.22) ** 2)
        if y > island_top and abs(x - 1.5) < 0.42:
            return pal.path("w6 w4 x4 -")((y - island_top) * 8), 1.0, True, "sand"
        if y >= hz:
            t = (y - hz) / (1 - hz)
            c = sea(t)
            near = abs(x - sun_x) < 0.13 * (1 - t * 0.5) + 0.02
            ripple = math.sin(x * 50 + y * 300 + 3 * math.sin(x * 9)) > 0.35
            if near and ripple and math.sin(y * 170) > -0.2:
                c = mix(c, pal.rgb("w8"), 0.85 - t * 0.6)          # the sun's path
            elif ripple and t > 0.1:
                c = mix(c, pal.rgb("a6"), 0.25)
            return c, 1.0, False, "sea"
        d = math.hypot(x - sun_x, y - sun_y)
        if d <= sun_r:
            return sun((y - sun_y + sun_r) / (2 * sun_r)), 1.0, True, "sun"
        t = y / hz
        c = sky(min(1.0, t + math.exp(-(d / 0.45) ** 2) * 0.25))
        k = cloud(x, y)
        if k:
            lit = mix(pal.rgb("x4"), pal.rgb("e8"), max(0.0, min(1.0, 1.2 - (y - 0.2) * 4)))
            c = mix(c, lit, min(1.0, k * 1.5))
        return c, 1.0, False, "sky"

    def lines(rows):
        return [([(-6.0, hz + 0.002), (2.0, hz + 0.002)], pal.rgb("w6"), False, None)]

    def texts(rows, x_left, cw, unit):
        out = []
        for x, y in ((0.95, 0.12), (1.05, 0.16), (1.12, 0.1), (-0.4, 0.18), (-0.3, 0.14)):
            out.append((int((x - x_left) / cw), int(y / unit), "v", pal.rgb("d1"), x > 0))
        return out

    return Scene(1.9, field, lines, texts, span=True, sizes=SIZES, shade_cost=SHADE, theme="ocean")


# ---------------------------------------------------------------- midnight

def moon(pal):
    mx, my, mr = 1.25, 0.33, 0.2
    sky = pal.path("- a1 a1 a4")
    light = sphere_light(mx, my, mr, -0.6, -0.45)
    face = pal.path("d4 d6 t4 t8 w9")
    craters = [(mx - 0.06, my - 0.05, 0.05), (mx + 0.07, my + 0.07, 0.035), (mx - 0.09, my + 0.1, 0.03),
               (mx + 0.03, my - 0.11, 0.025), (mx + 0.1, my - 0.02, 0.02)]
    base = 0.97
    rnd = random.Random(5)
    blocks = []                                  # buildings: (x0, x1, top)
    x = 1.95
    while x > -3.5:
        w = rnd.uniform(0.07, 0.16)
        blocks.append((x - w, x, base - rnd.uniform(0.08, 0.3)))
        x -= w + rnd.uniform(0.0, 0.02)

    def building(x, y):
        for x0, x1, top in blocks:
            if x0 <= x <= x1 and y >= top:
                return x0, x1, top
        return None

    def cloud(x, y):
        for cx, cy, w, h in ((1.05, 0.45, 0.4, 0.04), (1.5, 0.52, 0.35, 0.03), (0.4, 0.3, 0.5, 0.03),
                             (-0.8, 0.38, 0.6, 0.035), (-2.2, 0.32, 0.5, 0.03)):
            d = ((x - cx) / w) ** 2 + ((y - cy) / h) ** 2 + 0.25 * math.sin(x * 40) * 0.1
            if d < 1:
                return 1 - d
        return 0.0

    def field(x, y):
        b = building(x, y)
        if b:
            x0, x1, top = b
            cx, cy = (x - x0) / 0.025, (y - top) / 0.05
            window = (cx % 1 < 0.5) and (cy % 1 < 0.45) and y > top + 0.03 and x0 + 0.015 < x < x1 - 0.015
            lit = window and random.Random(int(cx) * 7919 + int(cy) * 31 + int(x0 * 1000)).random() < 0.35
            return (pal.rgb("w8") if lit else pal.rgb("a1") if window else pal.ground), 1.0, False, "city"
        d = math.hypot(x - mx, y - my)
        if d <= mr:
            t = light(x, y)
            for kx, ky, kr in craters:
                q = math.hypot(x - kx, y - ky) / kr
                if q < 1:
                    t -= 0.25 * (1 - q * 0.6)
            return face(max(0.0, min(1.0, t))), 1.0, True, "moon"
        c = sky(min(1.0, y * 1.1))
        halo = math.exp(-((d - mr) / 0.12) ** 2) * 0.55
        c = mix(c, pal.rgb("a6"), halo)
        k = cloud(x, y)
        if k:
            rim = math.exp(-((d - mr) / 0.25) ** 2)
            c = mix(c, mix(pal.rgb("a1"), pal.rgb("t6"), rim), min(1.0, k * 1.6))
            return c, 1.0, False, "cloud"
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        cols = [pal.rgb("t8"), pal.rgb("t9"), pal.rgb("a8"), pal.rgb("w9")]
        return stars(field, rows, x_left, cw, unit, rows * 9, 0.7, cols, 3)

    return Scene(1.9, field, None, texts, span=True, sizes=SIZES, shade_cost=SHADE, theme="midnight")


# ---------------------------------------------------------------- forest

def pines(pal):
    sky = pal.path("a1 d4 a4 w4 w6")
    far = ridge([(0.2, 0.5, 0.2), (0.9, 0.45, 0.26), (1.6, 0.5, 0.2), (-0.7, 0.6, 0.22), (-1.8, 0.6, 0.18)], 0.62)
    mid = ridge([(0.5, 0.35, 0.12), (1.25, 0.4, 0.16), (-0.3, 0.4, 0.12), (-1.3, 0.5, 0.14)], 0.72)
    rnd = random.Random(8)
    rows_of_trees = []
    for depth, (y0, h, w, n) in enumerate(((0.74, 0.12, 0.045, 60), (0.86, 0.2, 0.07, 30))):
        trees = [pine(rnd.uniform(-3.5, 2.0), y0 + rnd.uniform(-0.02, 0.03), h * rnd.uniform(0.7, 1.2),
                      w * rnd.uniform(0.8, 1.2)) for _ in range(n)]
        rows_of_trees.append(trees)
    hero = [pine(1.45, 1.02, 0.78, 0.2, 7), pine(1.72, 1.02, 0.56, 0.15, 6), pine(1.2, 1.02, 0.42, 0.12, 5)]
    mx, my, mr = 0.55, 0.2, 0.06

    def mist(y, at, width):
        return math.exp(-((y - at) / width) ** 2)

    def field(x, y):
        if any(t(x, y) for t in hero):
            c = pal.ground
            if not any(t(x + 0.01, y) for t in hero):
                c = pal.rgb("g1")                  # a little light on the right edges
            return c, 1.0, True, "tree"
        if y > 0.96:
            return pal.path("g1 -")((y - 0.96) * 20), 1.0, False, "ground"
        if any(t(x, y) for t in rows_of_trees[1]):
            return pal.rgb("g1"), 1.0, False, "trees"
        if any(t(x, y) for t in rows_of_trees[0]):
            return mix(pal.rgb("d4"), pal.rgb("g4"), 0.3), 1.0, False, "trees"
        if y >= mid(x):
            c = pal.path("a4 d4 g1")((y - mid(x)) * 6)
            return mix(c, pal.rgb("t4"), mist(y, 0.74, 0.03) * 0.5), 1.0, False, "hills"
        if y >= far(x):
            c = pal.path("d6 a4 d4")((y - far(x)) * 4)
            return mix(c, pal.rgb("t4"), mist(y, 0.62, 0.04) * 0.6), 1.0, False, "mountains"
        d = math.hypot(x - mx, y - my)
        if d <= mr:
            return pal.path("t9 t8 w8")((y - my + mr) / (2 * mr)), 1.0, True, "moon"
        c = sky(min(1.0, y * 1.35))
        c = mix(c, pal.rgb("t6"), math.exp(-(d / 0.18) ** 2) * 0.35)
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 4, 0.3, [pal.rgb("t8"), pal.rgb("w8")], 9,
                     chars="..·'")

    return Scene(1.9, field, None, texts, span=True, sizes=SIZES, shade_cost=SHADE, theme="forest")


# ---------------------------------------------------------------- ember

def fire(pal):
    fx, ground_y = 1.25, 0.84

    def flame(x, y):
        """0..1 heat inside the fire (0 outside): tongues flickering up."""
        t = (ground_y - y) / 0.62
        if t < 0 or t > 1:
            return 0.0
        best = 0.0
        for dx, w, h, ph in ((0.0, 0.17, 1.0, 0.0), (-0.09, 0.09, 0.62, 1.7), (0.1, 0.08, 0.55, 3.1),
                             (0.04, 0.06, 0.8, 4.2), (-0.04, 0.05, 0.7, 5.3)):
            u = t / h
            if u > 1:
                continue
            mid = fx + dx + 0.035 * u * math.sin(u * 9 + ph)
            half = w * (1 - u) ** 0.65 * min(1.0, 0.5 + u * 3) * (1 + 0.25 * math.sin(u * 20 + ph))
            q = 1 - abs(x - mid) / half if half > 0 else 0
            if q > 0:
                best = max(best, q * (1 - u * 0.4))
        return best

    heat = pal.path("e1 e4 e6 a6 w6 w8 t9")
    logs = [((fx - 0.3, ground_y + 0.07), (fx + 0.28, ground_y - 0.02)),
            ((fx + 0.3, ground_y + 0.07), (fx - 0.28, ground_y - 0.02))]
    trees = [pine(x, 0.86, h, w, 6) for x, h, w in ((0.25, 0.6, 0.14), (0.05, 0.45, 0.1),
                                                   (1.85, 0.66, 0.16), (-0.9, 0.5, 0.12),
                                                   (-1.6, 0.6, 0.14), (-2.4, 0.45, 0.1))]

    def log_at(x, y):
        for (ax, ay), (bx, by) in logs:
            dx, dy = bx - ax, by - ay
            u = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
            if math.hypot(x - ax - dx * u, y - ay - dy * u) < 0.028:
                return u
        return None

    def field(x, y):
        h = flame(x, y)
        if h > 0.02:
            return heat(min(1.0, h * 1.25)), 1.0, True, "fire"
        u = log_at(x, y)
        if u is not None:
            ends = min(u, 1 - u)
            return pal.path("x4 x1 d1")(min(1.0, ends * 3)), 1.0, True, "log"
        glow = math.exp(-((x - fx) / 0.45) ** 2 - ((y - ground_y) / 0.25) ** 2)
        if any(t(x, y) for t in trees):
            return mix(pal.ground, pal.rgb("x1"), glow * 0.8), 1.0, False, "tree"
        if y >= ground_y:
            c = pal.path("x1 d1 -")((y - ground_y) * 6)
            return mix(c, pal.rgb("a4"), glow * 0.75), 1.0, False, "ground"
        c = pal.path("- - x1 x1")(y)
        c = mix(c, pal.rgb("e4"), math.exp(-((x - fx) / 0.35) ** 2 - ((y - 0.6) / 0.35) ** 2) * 0.5)
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(4)
        out = stars(field, rows, x_left, cw, unit, rows * 5, 0.45, [pal.rgb("t6"), pal.rgb("d8")], 12,
                    chars="..·'")
        for _ in range(rows):                      # sparks rising from the fire
            y = rnd.uniform(0.05, 0.3)
            x = fx + rnd.gauss(0, 0.12) * (1 + (0.3 - y) * 2)
            out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("'.*`,"),
                        rnd.choice([pal.rgb("w9"), pal.rgb("a8"), pal.rgb("e8")]), True))
        return out

    return Scene(1.9, field, None, texts, span=True, sizes=SIZES, shade_cost=SHADE, theme="ember")


# ---------------------------------------------------------------- default

def keyboard(pal):
    """A keyboard on a desk at night, in the pool of light from a lamp:
    keycaps lit on top and shaded in front, letters on them, a few keys
    down."""
    rows_of_keys = ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    kw, kh, gap, rgap = 0.1, 0.1, 0.032, 0.055   # gaps wider than a character cell
    x0, y0 = 0.16, 0.1
    pressed = {"F", "J", "M"}
    keys_at = []
    for r, row in enumerate(rows_of_keys):
        for k, ch in enumerate(row):
            keys_at.append((x0 + r * kw * 0.45 + k * (kw + gap), y0 + r * (kh + rgap), ch))
    sy = y0 + 4 * (kh + rgap)
    space = (x0 + 0.45, sy, x0 + 0.45 + 5.4 * kw, kh * 0.9)
    body = (x0 - 0.06, y0 - 0.06, x0 + 10 * (kw + gap) + 0.12, sy + kh + 0.05)
    lamp = (0.75, -0.15)

    def lit(x, y):
        """How much lamp light falls here, 0..1."""
        return math.exp(-(((x - lamp[0]) / 0.85) ** 2 + ((y - lamp[1]) / 1.0) ** 2))

    def key_at(x, y):
        for kx, ky, ch in keys_at:
            if kx <= x <= kx + kw and ky <= y <= ky + kh:
                return kx, ky, ch
        sx, sy_, sx1, sh = space
        if sx <= x <= sx1 and sy_ <= y <= sy_ + sh:
            return sx, sy_, " "
        return None

    def field(x, y):
        light = lit(x, y)
        k = key_at(x, y)
        if k:
            kx, ky, ch = k
            down = ch in pressed
            v = (y - ky) / kh
            if v > 0.75:                          # the key's front, in shadow
                return pal.path("d1 d4")(light * 0.8), 1.0, True, "key"
            top = pal.path("d4 d6 t4 t8")(light * (0.85 if not down else 0.55) + 0.15 * (1 - v))
            return (mix(top, pal.rgb("g6"), 0.55) if down else top), 1.0, True, "key"
        bx0, by0, bx1, by1 = body
        if bx0 <= x <= bx1 and by0 <= y <= by1:
            edge = min(x - bx0, bx1 - x, y - by0, by1 - y)
            return pal.path("- d1 d4")(light * 0.9 + (0.15 if edge < 0.02 else 0)), 1.0, True, "case"
        if y > 0.9:                               # the desk
            grain = 0.5 + 0.5 * math.sin(x * 16 + 3 * math.sin(y * 50 + x * 2))
            return pal.path("- d1 d4 d6")(light * 1.2 * (0.7 + 0.3 * grain)), 1.0, False, "desk"
        if body[3] - 0.01 < y < 0.9 and body[0] < x < body[2] + 0.03:
            return pal.ground, 1.0, True, "shadow"
        # the room: dark, a little light from the lamp
        return pal.path("- d1")(light * 0.9), 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        out = []
        for kx, ky, ch in keys_at:
            col = int((kx + kw / 2 - x_left) / cw)
            row = int((ky + kh * 0.38) / unit)
            out.append((col, row, ch, pal.rgb("t9") if ch in pressed else pal.rgb("d1"), True))
        return out

    return Scene(1.9, field, None, texts, span=True, sizes=SIZES, shade_cost=SHADE, theme="default",
                 inks={"room": "d", "case": "d", "shadow": "d", "key": "dtg", "desk": "d"})


# ---------------------------------------------------------------- candy

def candy(pal):
    """Bubblegum pop: a big wrapped sweet, bow-tie shaped and pink all
    over - a round candy with a pink swirl and a shine, its wrapper twisted
    at both ends and fanning out in pleated wings; bubbles, sparkles and
    small sweets in a pink glow behind."""
    cx, cy, rx, ry = 1.2, 0.5, 0.25, 0.2
    knot = 0.035                                # the twist's half width
    wing = 0.34                                 # how far each wing reaches
    light = sphere_light(cx, cy, max(rx, ry), -0.5, -0.65)
    body = pal.path("a4 a6 a8 a9 t8")      # all pink: bubblegum
    stripe = pal.path("a1 a4 a6 a8")
    wrap = pal.path("a1 a4 a6 a8 a9")

    def wing_at(x, y):
        """0..1 along a wing (0 at the twist) and the pleat shading, or
        None outside the wings."""
        for side in (-1, 1):
            kx = cx + side * (rx + knot)
            t = (x - kx) * side / wing          # 0 at the twist .. 1 at the edge
            if not 0 <= t <= 1:
                continue
            ang = math.atan2(y - cy, (x - kx) * side)
            half = 0.045 + t * 0.19
            edge = half - (0.018 * abs(math.sin(ang * 9)) if t > 0.8 else 0)
            if abs(y - cy) <= edge and not (t > 0.97 and abs(math.sin(ang * 9)) > 0.6):
                pleat = 0.5 + 0.5 * math.sin(ang * 18)
                return t, pleat
        return None

    def upright(x, y):
        dx, dy = (x - cx) / rx, (y - cy) / ry
        r = math.hypot(dx, dy)
        if r <= 1:
            lit = light(x, y)
            swirl = math.sin(math.atan2(dy, dx) * 3 + r * 7) > 0.55
            c = stripe(lit) if swirl else body(lit)
            sx, sy = (x - (cx - rx * 0.4)) / (rx * 0.25), (y - (cy - ry * 0.5)) / (ry * 0.18)
            if sx * sx + sy * sy <= 1:
                c = pal.rgb("t9")                 # the shine
            return c, 1.0, True, "candy"
        for side in (-1, 1):                      # the twists
            kx = cx + side * (rx + knot * 0.6)
            if abs(x - kx) <= knot and abs(y - cy) <= 0.05 - abs(x - kx) * 0.4:
                return pal.rgb("a1"), 1.0, True, "wrap"
        w = wing_at(x, y)
        if w:
            t, pleat = w
            return wrap(0.25 + 0.55 * pleat * (1 - t * 0.35) + 0.2 * (1 - t)), 1.0, True, "wrap"
        glow = math.exp(-(((x - cx) / 0.75) ** 2 + ((y - cy) / 0.45) ** 2))
        return pal.path("- a1")(glow * 0.4), 1.0, False, "bg"

    tilt = math.radians(-22)                    # the sweet lies at an angle
    ct, st_ = math.cos(tilt), math.sin(tilt)

    def field(x, y):
        """The upright sweet, turned: look up where this point was before
        the turn."""
        u, v = x - cx, y - cy
        return upright(cx + u * ct + v * st_, cy - u * st_ + v * ct)

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(21)
        out = []
        for _ in range(rows * 3):
            x, y = rnd.uniform(-3.0, 1.9), rnd.uniform(0.0, 0.98)
            if field(x, y)[3] != "bg":
                continue
            out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("+*.·'oO°"),
                        rnd.choice([pal.rgb("t8"), pal.rgb("a8"), pal.rgb("a6"), pal.rgb("a9")]), False))
        for k in range(6):                        # little wrapped sweets
            x, y = -2.6 + k * 0.5 + rnd.uniform(-0.1, 0.1), rnd.uniform(0.15, 0.85)
            if field(x, y)[3] != "bg" or field(x + 0.12, y)[3] != "bg":
                continue
            c0 = int((x - x_left) / cw)
            for j, ch in enumerate("><(@)><"):
                out.append((c0 + j, int(y / unit), ch,
                            pal.rgb("a9") if ch == "@" else pal.rgb("a6"), False))
        return out

    return Scene(1.9, field, None, texts, span=True, sizes=SIZES, shade_cost=SHADE, theme="candy",
                 inks={"candy": "at", "wrap": "a", "bg": "a"})


WOW = {"island": island, "moon": moon, "pines": pines, "fire": fire, "keyboard": keyboard,
       "lollipop": candy}
