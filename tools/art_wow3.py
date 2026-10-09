"""More "wow" pictures (see art_wow.py, art_wow2.py): nature themes -
jungle, cherry blossom, lavender, tundra, coral reef, volcanic, bamboo,
dracula, nord, gruvbox, solarized, monokai, catppuccin, rose pine."""

import math
import random

from art_combined import mix
from art_wow import ridge, sphere_light, stars
from art_wow2 import clamp, fbm, noise, scene, soft_clouds


# ---------------------------------------------------------------- shapes

def poly(points):
    """Inside a polygon (even-odd rule)."""
    def inside(x, y):
        hit = False
        for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
            if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                hit = not hit
        return hit
    return inside


def strokes(paths):
    """Thick polylines: paths [(points, width at start, width at end)];
    inside(x, y) -> 0..1 along the stroke it's in, or None."""
    segs = []
    for pts, w0, w1 in paths:
        n = len(pts) - 1
        for k, (a, b) in enumerate(zip(pts, pts[1:])):
            segs.append((a, b, w0 + (w1 - w0) * k / n, w0 + (w1 - w0) * (k + 1) / n, k / n, (k + 1) / n))

    def inside(x, y):
        for (ax, ay), (bx, by), ra, rb, ta, tb in segs:
            dx, dy = bx - ax, by - ay
            u = clamp(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy or 1e-9))
            r = ra + (rb - ra) * u
            if (x - ax - dx * u) ** 2 + (y - ay - dy * u) ** 2 <= r * r:
                return ta + (tb - ta) * u
        return None
    return inside


def bezier(p0, p1, p2, n=16):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (k / n for k in range(n + 1))]


def disc(cx, cy, r):
    return lambda x, y: math.hypot(x - cx, y - cy) <= r


# ---------------------------------------------------------------- jungle

def jungle(pal):
    """A waterfall dropping through the jungle into a misty pool, huge
    leaves and vines in front, magenta flowers."""
    fx = 1.0
    sky = pal.path("d4 a4 t4")
    leaves = []
    for cx, cy, ang, ln in ((1.55, 0.55, -40, 0.42), (1.75, 0.35, -75, 0.36), (1.4, 0.8, -15, 0.38),
                            (1.85, 0.75, -110, 0.3), (0.62, 0.86, -160, 0.32)):
        a = math.radians(ang)
        leaves.append((cx, cy, math.cos(a), math.sin(a), ln))
    vines = strokes([(bezier((x, -0.05), (x + 0.05, 0.3), (x - 0.02, 0.2 + h)), 0.008, 0.005)
                     for x, h in ((0.35, 0.4), (0.8, 0.25), (1.25, 0.35), (-0.4, 0.45), (-1.3, 0.3), (-2.2, 0.4))])

    def leaf_at(x, y):
        for cx, cy, dx, dy, ln in leaves:
            u = (x - cx) * dx + (y - cy) * dy * 2
            v = -(x - cx) * dy + (y - cy) * dx * 2 * 0.5
            if 0 <= u <= ln:
                half = ln * 0.32 * math.sin(math.pi * u / ln) ** 0.8
                if abs(v) <= half and not (abs(v) > half * 0.35 and math.sin(u * 60) > 0.75):
                    return u / ln, v / (half or 1)
        return None

    def field(x, y):
        lf = leaf_at(x, y)
        if lf:
            u, v = lf
            c = pal.path("d1 g1 a4 g4 g6")(clamp(0.45 + v * 0.3 + (1 - u) * 0.2))
            if abs(v) < 0.08:
                c = pal.rgb("t4")                              # the midrib
            return c, 1.0, True, "leaf"
        if vines(x, y) is not None:
            return pal.rgb("d4"), 1.0, False, "vine"
        if abs(x - fx - 0.02 * math.sin(y * 9)) < 0.09 and 0.16 < y < 0.8:
            streak = math.sin(x * 260 + y * 30) * 0.5 + 0.5
            return pal.path("a4 t4 t6 t9")(clamp(0.5 + streak * 0.5 - abs(x - fx) * 3)), 1.0, True, "fall"
        if y > 0.78:
            foam = math.exp(-((x - fx) / 0.25) ** 2) * math.exp(-((y - 0.8) / 0.05) ** 2)
            c = pal.path("a4 d4 d1 -")(clamp((y - 0.78) * 4))
            return mix(c, pal.rgb("t8"), foam), 1.0, False, "pool"
        cliff = abs(x - fx) < 0.3 and y > 0.14 + 0.05 * math.sin(x * 20)
        if cliff:
            return pal.path("- d1 d4")(fbm(x * 20, y * 20, 2)), 1.0, False, "cliff"
        foliage = fbm(x * 3.5, y * 5, 6, 4)
        if foliage > 0.42 + y * 0.12:
            c = pal.path("- d1 g1 a4 g4")(clamp((foliage - 0.4) * 2.2 + (1 - y) * 0.2))
            return c, 1.0, False, "canopy"
        mist = math.exp(-((y - 0.7) / 0.15) ** 2)
        return mix(sky(clamp(y * 1.2)), pal.rgb("t6"), mist * 0.4), 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(31)
        out = []
        for _ in range(rows):
            x, y = rnd.uniform(-3.0, 1.9), rnd.uniform(0.2, 0.9)
            if field(x, y)[3] == "canopy":
                out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("*@"),
                            rnd.choice([pal.rgb("e6"), pal.rgb("e8"), pal.rgb("w8")]), False))
        return out

    return scene("jungle", field, texts)


# ---------------------------------------------------------------- cherry blossom

def blossom(pal):
    """A cherry tree in full bloom, petals drifting, a snow-capped
    mountain behind in a pale pink dawn."""
    sky = pal.path("d4 a4 a6 t6 t8")
    mount = ridge([(0.4, 0.75, 0.38), (-1.6, 0.8, 0.2)], 0.72)
    trunk = strokes([
        (bezier((1.42, 0.98), (1.48, 0.7), (1.35, 0.5)), 0.05, 0.03),
        (bezier((1.38, 0.55), (1.15, 0.45), (0.95, 0.38)), 0.025, 0.01),
        (bezier((1.36, 0.52), (1.55, 0.35), (1.75, 0.3)), 0.022, 0.01),
        (bezier((1.4, 0.7), (1.65, 0.62), (1.85, 0.55)), 0.02, 0.008),
        (bezier((1.35, 0.5), (1.3, 0.3), (1.25, 0.2)), 0.02, 0.008)])
    crowns = [(1.0, 0.36, 0.2), (1.25, 0.24, 0.22), (1.55, 0.27, 0.22), (1.78, 0.42, 0.18),
              (1.4, 0.4, 0.2), (1.12, 0.48, 0.14)]

    def crown(x, y):
        best = -1.0
        for cx, cy, r in crowns:
            d = math.hypot(x - cx, (y - cy) * 1.6) / r
            best = max(best, 1 - d)
        return best + (fbm(x * 18, y * 30, 3) - 0.5) * 0.5

    def field(x, y):
        k = crown(x, y)
        if k > 0:
            light = clamp(0.4 + k * 0.6 + (0.3 - y) * 0.8 + fbm(x * 30, y * 50, 8) * 0.3)
            return pal.path("x4 a4 a6 a8 t9")(light), 1.0, True, "bloom"
        if trunk(x, y) is not None:
            return pal.path("- d1")(0.4), 1.0, True, "tree"
        if y > 0.9:
            return pal.path("g4 g1 -")(clamp((y - 0.9) * 8)), 1.0, False, "ground"
        top = mount(x)
        if y >= top:
            snow = y - top < 0.06 + 0.02 * math.sin(x * 40)
            return (pal.path("t8 t6")((y - top) * 10) if snow else pal.path("d4 d1")((y - top) * 3)), 1.0, False, "mountain"
        c = sky(clamp(y * 1.3))
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(13)
        out = []
        for _ in range(rows * 3):
            x, y = rnd.uniform(-3.0, 1.9), rnd.uniform(0.05, 0.95)
            if field(x, y)[3] in ("sky", "mountain", "ground"):
                out.append((int((x - x_left) / cw), int(y / unit), rnd.choice(".,'`*"),
                            rnd.choice([pal.rgb("a8"), pal.rgb("a6"), pal.rgb("t9")]), False))
        return out

    return scene("cherry blossom", field, texts, inks={"bloom": "atx", "sky": "datw"})


# ---------------------------------------------------------------- lavender

def lavender(pal):
    """Rows of lavender running to the horizon under a golden evening,
    a lone tree on the rise."""
    hz = 0.55
    sky = pal.path("d4 a4 e6 w6 w8")
    tree_c = [(1.45, 0.36, 0.13), (1.36, 0.42, 0.1), (1.56, 0.43, 0.1), (1.45, 0.47, 0.09)]
    trunk = strokes([([(1.45, 0.6), (1.45, 0.42)], 0.015, 0.01)])

    def field(x, y):
        for cx, cy, r in tree_c:
            if math.hypot(x - cx, (y - cy) * 1.5) < r + 0.02 * noise(x * 40, y * 40):
                rim = math.hypot(x - cx - 0.02, (y - cy + 0.02) * 1.5) > r * 0.9
                return (pal.rgb("g4") if rim else pal.path("- g1")(0.6)), 1.0, True, "tree"
        if trunk(x, y) is not None:
            return pal.ground, 1.0, True, "tree"
        if y < hz:
            d = math.hypot(x - 0.6, y - hz)
            c = sky(clamp(y / hz + math.exp(-(d / 0.4) ** 2) * 0.3))
            k = soft_clouds([(0.3, 0.22, 0.5, 0.03), (1.3, 0.15, 0.4, 0.025), (-1.0, 0.25, 0.6, 0.03)])(x, y)
            return mix(c, pal.rgb("e6"), clamp(k * 1.2)), 1.0, False, "sky"
        t = (y - hz) / (1 - hz)
        vx = 0.6
        rowpos = (x - vx) / (t + 0.02) * 6
        row = math.cos(rowpos * math.pi * 2) * 0.5 + 0.5
        if row > 0.35:
            light = clamp(row * 0.8 + t * 0.2)
            c = pal.path("x1 d4 a4 a6 a8")(light)
            if t > 0.5 and noise(x * 120, y * 80) > 0.65:
                c = pal.rgb("a9")
            return c, 1.0, False, "field"
        return pal.path("g4 g1 -")(t), 1.0, False, "field"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 2, 0.2, [pal.rgb("t8")], 5, chars="..·")

    return scene("lavender", field, texts)


# ---------------------------------------------------------------- tundra

def snowpeaks(pal):
    """A great snowy peak lit on one side, icy blue in shadow, ranges
    behind, a snowfield with drifts and a moon in a cold sky."""
    main = ridge([(1.35, 0.6, 0.62), (1.0, 0.3, 0.3), (1.75, 0.35, 0.36)], 0.85)
    back = ridge([(0.3, 0.6, 0.4), (-0.8, 0.7, 0.45), (-2.2, 0.7, 0.4), (0.9, 0.4, 0.3)], 0.78)
    sky = pal.path("d1 a1 a4 g4 t4")
    mx, my, mr = 0.45, 0.18, 0.06

    def field(x, y):
        top = main(x)
        if y >= top and y < 0.86 and top < 0.84:
            peak = 1.35
            lit = x < peak + (y - top) * 0.3
            depth = y - top
            if lit:
                c = pal.path("t9 t8 t6 a6")(clamp(depth * 2.5 + fbm(x * 25, y * 25) * 0.25))
            else:
                c = pal.path("a4 a1 d4 d1")(clamp(depth * 2 + fbm(x * 25, y * 25) * 0.3))
            if fbm(x * 12, y * 6, 4) > 0.68 and depth > 0.05:
                c = mix(c, pal.rgb("d1"), 0.6)                # rock showing through
            return c, 1.0, True, "peak"
        if y >= 0.85:
            drift = math.sin(x * 14 + math.sin(x * 3) * 2) * 0.5 + 0.5
            return pal.path("t8 t6 a6 a4 d4")(clamp((y - 0.85) * 4 + drift * 0.25)), 1.0, False, "snow"
        btop = back(x)
        if y >= btop:
            return pal.path("a4 a1 d4")(clamp((y - btop) * 3)), 1.0, False, "range"
        d = math.hypot(x - mx, y - my)
        if d <= mr:
            return pal.path("t9 t8")(clamp((y - my) / mr)), 1.0, False, "moon"
        c = sky(clamp(y * 1.25))
        return mix(c, pal.rgb("t6"), math.exp(-(d / 0.2) ** 2) * 0.3), 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        out = stars(field, rows, x_left, cw, unit, rows * 6, 0.5, [pal.rgb("t9"), pal.rgb("a8")], 21)
        rnd = random.Random(2)
        for _ in range(rows * 2):                  # snowflakes
            x, y = rnd.uniform(-3, 1.9), rnd.uniform(0, 0.95)
            out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("·.*"), pal.rgb("t9"),
                        field(x, y)[2]))
        return out

    return scene("tundra", field, texts, inks={"peak": "tagd", "sky": "dagt", "snow": "tad"})


# ---------------------------------------------------------------- coral reef

def reef(pal):
    """Underwater: branching corals and a big round brain coral, fish,
    light falling in shafts from the surface, bubbles rising."""
    water = pal.path("g6 g4 g1 d1 -")
    branches = []
    rnd = random.Random(4)
    for bx, h in ((1.15, 0.38), (1.55, 0.3), (1.8, 0.42), (0.85, 0.25)):
        def grow(x, y, ang, ln, w, depth):
            ex, ey = x + math.cos(ang) * ln, y - math.sin(ang) * ln
            branches.append(([(x, y), (ex, ey)], w, w * 0.7))
            if depth:
                for d in (-0.5, 0.45):
                    grow(ex, ey, ang + d + rnd.uniform(-0.15, 0.15), ln * 0.72, w * 0.7, depth - 1)
        grow(bx, 0.95, math.pi / 2, h * 0.45, 0.025, 3)
    coral = strokes(branches)
    brain = (1.38, 0.88, 0.14)

    def fish(x, y):
        for fx_, fy_, s, flip in ((0.6, 0.45, 0.06, 1), (1.4, 0.3, 0.05, -1), (0.2, 0.62, 0.04, 1),
                                  (-1.0, 0.4, 0.05, -1), (-2.0, 0.55, 0.05, 1)):
            u, v = (x - fx_) / s * flip, (y - fy_) / s * 2
            if u * u + v * v * 1.3 <= 1 or (-1.6 < u < -0.9 and abs(v) < (-0.9 - u) * 1.4):
                stripe = abs(u - 0.2) < 0.15 or abs(u + 0.45) < 0.12
                return stripe
        return None

    def field(x, y):
        bx, by, br = brain
        if math.hypot(x - bx, (y - by) * 1.4) <= br and y < 0.97:
            light = sphere_light(bx, by, br)(x, by + (y - by) * 1.4)
            groove = math.sin((x - bx) * 90 + math.sin((y - by) * 60) * 2) > 0.5
            return pal.path("x1 e4 a4 a6 w6")(clamp(light * 0.9 - (0.2 if groove else 0))), 1.0, True, "coral"
        t = coral(x, y)
        if t is not None:
            return pal.path("e4 e6 a6 a8")(clamp(t * 0.8 + 0.2)), 1.0, True, "coral"
        f = fish(x, y)
        if f is not None:
            return (pal.rgb("t8") if f else pal.rgb("w6")), 1.0, x > 0.4, "fish"
        if y > 0.93:
            return pal.path("w4 x1 -")(clamp((y - 0.93) * 12 + noise(x * 50, 3) * 0.3)), 1.0, False, "sand"
        shaft = clamp(math.sin((x + y * 0.35) * 7) * 0.5 + 0.5) ** 8 * (1 - y)
        c = water(clamp(y * 0.95 + fbm(x * 5, y * 8) * 0.1))
        return mix(c, pal.rgb("t6"), shaft * 0.5), 1.0, False, "water"

    def texts(rows, x_left, cw, unit):
        rnd2 = random.Random(8)
        out = []
        for _ in range(rows * 2):
            x, y = rnd2.uniform(-3, 1.9), rnd2.uniform(0.05, 0.85)
            if field(x, y)[3] == "water":
                out.append((int((x - x_left) / cw), int(y / unit), rnd2.choice("o°.·"), pal.rgb("t8"), False))
        return out

    return scene("coral reef", field, texts, inks={"water": "gdt", "coral": "eawx"})


# ---------------------------------------------------------------- volcanic

def volcano(pal):
    """A volcano erupting at night: a fountain of lava, glowing rivers
    down its flanks, an ash cloud lit from below, sparks."""
    cx = 1.3
    cone = ridge([(cx, 0.75, 0.55)], 0.95)

    def crater_top(x):
        return min(cone(x), 0.42 + abs(x - cx) * 0.3) if abs(x - cx) < 0.09 else cone(x)

    def lava_river(x, y):
        for k, ph in ((-1, 0.0), (1, 1.5), (-1, 3.0)):
            path_x = cx + k * (y - 0.42) * (0.7 + 0.2 * ph) + 0.03 * math.sin(y * 25 + ph)
            if abs(x - path_x) < 0.012 + (y - 0.42) * 0.02:
                return clamp(1 - (y - 0.42) * 1.2)
        return None

    def field(x, y):
        # the fountain
        t = (0.42 - y) / 0.3
        if 0 < t < 1 and abs(x - cx - 0.02 * math.sin(t * 9)) < 0.06 * (1 - t) ** 0.7 + 0.01:
            return pal.path("x4 e6 a6 w8 w9")(clamp(1 - t * 0.6)), 1.0, True, "lava"
        top = crater_top(x)
        if y >= top:
            r = lava_river(x, y)
            if r is not None:
                return pal.path("e4 e6 a6 w8")(r), 1.0, True, "lava"
            glow = math.exp(-((x - cx) / 0.3) ** 2 - ((y - 0.45) / 0.2) ** 2)
            rock = fbm(x * 20, y * 20, 3)
            c = mix(pal.path("- x1 d1")(rock * 0.8), pal.rgb("e4"), glow * 0.6)
            return c, 1.0, abs(x - cx) < 0.6 and y < 0.88, "cone"
        cloud = fbm(x * 3, y * 4, 9, 4) * clamp(1.2 - y * 1.8) * math.exp(-((x - cx - 0.3 + y * 0.6) / 1.1) ** 2)
        lit = math.exp(-((x - cx) / 0.5) ** 2 - ((y - 0.35) / 0.3) ** 2)
        c = pal.path("- x1")(clamp(y * 0.8 + lit * 0.6))
        if cloud > 0.25:
            c = mix(pal.path("- d1 x4")(lit), pal.rgb("e4"), lit * 0.5)
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(6)
        out = stars(field, rows, x_left, cw, unit, rows * 2, 0.4, [pal.rgb("t6")], 12, chars="..·")
        for _ in range(rows * 2):
            y = rnd.uniform(0.02, 0.4)
            x = cx + rnd.gauss(0, 0.15) * (1 + (0.4 - y) * 3)
            out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("'.*`,"),
                        rnd.choice([pal.rgb("w9"), pal.rgb("a8"), pal.rgb("e8")]), y > 0.1))
        return out

    return scene("volcanic", field, texts)


# ---------------------------------------------------------------- bamboo

def bamboo(pal):
    """A bamboo grove: tall jointed stalks in front, rows fading into
    the mist behind, leaves in fans, soft light."""
    rnd = random.Random(17)
    stalks = []
    for depth, n, w in ((0, 40, 0.012), (1, 22, 0.02), (2, 7, 0.035)):
        for _ in range(n):
            x = rnd.uniform(-3.2, 1.95) if depth < 2 else rnd.uniform(0.95, 1.95)
            stalks.append((x, w * rnd.uniform(0.8, 1.2), depth, rnd.uniform(0, 1)))
    stalks.sort(key=lambda s: -s[2])

    def leafy(x, y, seed):
        return fbm(x * 10, y * 14, seed) > 0.62 and y < 0.5

    def field(x, y):
        for sx, w, depth, ph in stalks:
            lean = (1 - y) * 0.03 * math.sin(ph * 6)
            if abs(x - sx - lean) < w:
                joint = (y * (6 + depth * 2) + ph) % 1 < 0.06
                light = 0.5 + 0.5 * (sx - x + lean) / w
                if depth == 2:
                    c = pal.path("g1 g4 a6 w6")(clamp(light * 0.8 + 0.1))
                    if joint:
                        c = pal.rgb("g1")
                    return c, 1.0, 0.1 < y < 0.88, "stalk"
                base = pal.path("d1 g1 g4")(clamp(0.3 + light * 0.4 - depth * 0.15))
                return mix(base, pal.rgb("t4"), 0.45 - depth * 0.2), 1.0, False, "grove"
        if leafy(x, y, 3) and x > 0.9:
            return pal.path("g1 a4 g6")(fbm(x * 30, y * 30, 5)), 1.0, True, "leaves"
        if leafy(x, y + 0.1, 7):
            return mix(pal.rgb("g4"), pal.rgb("t4"), 0.5), 1.0, False, "grove"
        if y > 0.92:
            return pal.path("g1 d1 -")((y - 0.92) * 10), 1.0, False, "ground"
        mist = pal.path("t6 t4 a4 g4 d1")(clamp(y * 0.9))
        return mist, 1.0, False, "mist"

    return scene("bamboo", field, inks={"mist": "tagdw", "stalk": "gaw"})


# ---------------------------------------------------------------- dracula

def bat(pal):
    """A castle on a crag against a huge full moon, bats streaming out,
    thin clouds across the moon."""
    mx, my, mr = 1.25, 0.38, 0.27
    face = pal.path("a4 d6 t6 t8 t9")
    light = sphere_light(mx, my, mr, -0.3, -0.4)
    sky = pal.path("- d1 a1 d4 a4")
    castle = poly([(0.95, 0.95), (0.95, 0.66), (0.99, 0.66), (0.99, 0.6), (1.02, 0.55), (1.05, 0.6),
                   (1.05, 0.66), (1.12, 0.66), (1.12, 0.52), (1.16, 0.44), (1.2, 0.52), (1.2, 0.62),
                   (1.28, 0.62), (1.28, 0.7), (1.36, 0.7), (1.36, 0.56), (1.39, 0.5), (1.42, 0.56),
                   (1.42, 0.72), (1.5, 0.72), (1.5, 0.95)])
    crag = ridge([(1.2, 0.5, 0.2), (1.7, 0.3, 0.1), (0.6, 0.4, 0.08)], 0.98)

    def bat_at(x, y):
        for bx, by, s in ((1.1, 0.28, 0.07), (1.45, 0.2, 0.05), (0.75, 0.32, 0.045), (1.62, 0.36, 0.04),
                          (0.4, 0.2, 0.035), (-0.3, 0.3, 0.03), (-1.3, 0.22, 0.03)):
            u, v = (x - bx) / s, (y - by) / s * 2
            wing = abs(u) < 1 and -0.1 + 0.35 * abs(u) - 0.25 * abs(math.sin(abs(u) * 6)) * (abs(u) > 0.3) < v < 0.15 + 0.3 * abs(u) ** 2
            body = u * u * 6 + (v - 0.15) ** 2 * 3 < 0.25
            if wing or body:
                return True
        return False

    def field(x, y):
        if castle(x, y) or y >= crag(x):
            window = castle(x, y) and (int(x * 90) % 3 == 0) and (int(y * 40) % 4 == 1) and noise(x * 30, y * 30) > 0.55
            return (pal.rgb("w8") if window else pal.ground), 1.0, castle(x, y) or abs(x - 1.2) < 0.35, "castle"
        if bat_at(x, y):
            return pal.ground, 1.0, x > 0.9, "bat"
        d = math.hypot(x - mx, y - my)
        cloud = soft_clouds([(1.1, 0.45, 0.45, 0.02), (1.4, 0.33, 0.35, 0.015), (0.2, 0.3, 0.6, 0.02),
                             (-1.2, 0.4, 0.7, 0.025)])(x, y)
        if d <= mr:
            t = light(x, y) - 0.15 * (fbm(x * 12, y * 12, 4) > 0.6)
            c = face(clamp(t))
            return mix(c, pal.rgb("d4"), cloud * 0.8), 1.0, True, "moon"
        c = sky(clamp(y * 0.9))
        c = mix(c, pal.rgb("a4"), math.exp(-((d - mr) / 0.15) ** 2) * 0.6)
        return mix(c, pal.rgb("d4"), cloud * 0.7), 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 6, 0.7, [pal.rgb("t8"), pal.rgb("a8")], 13)

    return scene("dracula", field, texts, inks={"sky": "da", "moon": "tda"})


# ---------------------------------------------------------------- nord

def mountains(pal):
    """Arctic layers: ranges stepping back into cold haze, a snowy peak
    in front, a fjord below reflecting the pale sky, a cabin's light."""
    sky = pal.path("d1 d4 a4 a6 t6")
    layers = [ridge([(0.2, 0.6, 0.2), (1.0, 0.5, 0.25), (-1.0, 0.7, 0.22), (-2.3, 0.6, 0.2)], 0.55),
              ridge([(0.6, 0.5, 0.18), (-0.4, 0.6, 0.2), (-1.7, 0.6, 0.18)], 0.62),
              ridge([(1.35, 0.55, 0.5), (1.8, 0.3, 0.3), (0.9, 0.3, 0.2)], 0.72)]
    shore = 0.76

    def field(x, y):
        if y >= shore:
            my = shore - (y - shore) * 1.4 + 0.004 * math.sin(y * 260)
            c, _, _, _ = field(x, clamp(my, 0.0, shore - 0.001))
            return mix(c, pal.ground, 0.3 + (y - shore)), 1.0, False, "fjord"
        top = layers[2](x)
        if y >= top:
            lit = (x - 1.35) < (y - top) * 0.4
            snow = y - top < 0.12 + 0.03 * math.sin(x * 40) and top < 0.66
            if snow:
                c = pal.path("t8 t6 a6")(clamp((y - top) * 6)) if lit else pal.path("a6 a4 d4")((y - top) * 5)
            else:
                c = pal.path("d4 d1 -")(clamp((y - top) * 3))
            cabin = 1.05 < x < 1.1 and shore - 0.035 < y < shore
            if cabin:
                return (pal.rgb("w8") if 1.065 < x < 1.08 and y > shore - 0.025 else pal.ground), 1.0, True, "peak"
            return c, 1.0, abs(x - 1.35) < 0.5, "peak"
        for k, (layer, col) in enumerate(((layers[1], "a4"), (layers[0], "a6"))):
            if y >= layer(x):
                return mix(pal.rgb(col), pal.rgb("d4"), (y - layer(x)) * 2 + k * 0.1), 1.0, False, "range"
        return sky(clamp(y / shore)), 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 3, 0.3, [pal.rgb("t8")], 23, chars="..·")

    return scene("nord", field, texts, inks={"sky": "dat", "peak": "datw", "range": "dat"})


# ---------------------------------------------------------------- gruvbox

def coffee(pal):
    """A mug of coffee steaming on a wooden table in warm light, beans
    scattered, a window glow behind."""
    cx, top_y, bot_y, rw = 1.3, 0.38, 0.82, 0.2
    steam = [bezier((cx + dx, top_y - 0.03), (cx + dx + 0.1, top_y - 0.2), (cx + dx - 0.05, 0.05), 24)
             for dx in (-0.08, 0.0, 0.08)]

    def mug(x, y):
        if top_y <= y <= bot_y:
            w = rw * (1 - (y - top_y) * 0.12)
            if abs(x - cx) <= w:
                return (x - cx) / w
        # the handle
        hx, hy = cx + rw + 0.02, (top_y + bot_y) / 2 - 0.02
        d = math.hypot((x - hx) / 0.09, (y - hy) / 0.16)
        if 0.6 <= d <= 1 and x > cx + rw - 0.02:
            return 0.9
        return None

    def field(x, y):
        m = mug(x, y)
        if m is not None:
            if y < top_y + 0.035 and abs(x - cx) < rw * 0.9:
                return pal.path("x1 x4")(0.4 + (x - cx) * 2), 1.0, True, "coffee"   # the coffee
            light = clamp(0.75 - m * 0.45 + (0.3 if -0.6 < m < -0.35 else 0))
            return pal.path("x1 x4 a4 a6 w8")(light), 1.0, True, "mug"
        if y > 0.8:
            plank = math.sin(y * 120) > 0.92
            grain = fbm(x * 4, y * 40, 2)
            c = pal.path("- x1 a4 x4")(clamp(grain * 0.7 + (0.2 if not plank else -0.2)))
            shadow = math.exp(-((x - cx - 0.15) / 0.3) ** 2 - ((y - 0.84) / 0.03) ** 2)
            return mix(c, pal.ground, shadow * 0.7), 1.0, False, "table"
        window = -0.4 < x < 0.5 and 0.12 < y < 0.7
        if window and not (abs(x - 0.05) < 0.01 or abs(y - 0.4) < 0.01):
            return pal.path("a4 a6 w6 w8")(clamp(0.9 - y)), 1.0, False, "window"
        glow = math.exp(-((x - 0.05) / 0.9) ** 2 - ((y - 0.4) / 0.5) ** 2)
        return pal.path("- d1 x1 a4")(glow * 0.8), 1.0, False, "wall"

    def lines(rows):
        return [(pts, pal.rgb("t6"), False, None) for pts in steam]

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(1)
        out = []
        for _ in range(9):
            x, y = rnd.uniform(0.7, 1.85), rnd.uniform(0.86, 0.96)
            if mug(x, y) is None:
                out.append((int((x - x_left) / cw), int(y / unit), "0", pal.rgb("x4"), False))
        return out

    return scene("gruvbox", field, texts, lines, inks={"mug": "xaw", "wall": "dxa", "table": "xa"})


# ---------------------------------------------------------------- solarized

def sun(pal):
    """A huge sun rising over a lake: a blazing disc in a layered corona,
    rays fanning across a sky going from deep blue through magenta to
    orange, long clouds lit from below, ridges stepping back into the
    glow, all of it mirrored in the water with a glittering path, and
    reeds dark against the light in front."""
    sx, sy, sr = 1.2, 0.38, 0.13
    hz = 0.64
    sky = pal.path("a1 a2 a3 x3 x5 e5 e7 e9")
    disc = pal.path("t9 t9 w9 e9")
    ridges = [  # far to near: (top, colours, lit)
        (ridge([(0.7, 0.5, 0.15), (1.7, 0.45, 0.19), (-0.4, 0.6, 0.14), (1.3, 0.2, 0.09)], hz), "x1 x3 x4 e5", 0.35),
        (ridge([(0.3, 0.4, 0.11), (1.95, 0.4, 0.13), (-0.9, 0.5, 0.1), (1.1, 0.3, 0.05)], hz), "a1 x1 x2 x3", 0.25),
        (ridge([(-0.2, 0.45, 0.07), (0.75, 0.3, 0.05), (1.8, 0.3, 0.08)], hz), "- a1 x1 x2", 0.2)]
    clouds = soft_clouds([(0.95, 0.24, 0.45, 0.02), (1.6, 0.2, 0.3, 0.016), (1.0, 0.5, 0.55, 0.014),
                          (0.25, 0.33, 0.5, 0.022), (-0.5, 0.22, 0.6, 0.026), (1.75, 0.46, 0.25, 0.012),
                          (0.0, 0.47, 0.45, 0.016), (1.45, 0.3, 0.2, 0.012)])
    rnd = random.Random(12)
    reeds = [(rnd.uniform(1.45, 2.0), rnd.uniform(0.66, 0.82), rnd.uniform(-0.05, 0.05)) for _ in range(22)]
    reeds += [(rnd.uniform(-1.0, -0.6), rnd.uniform(0.75, 0.88), rnd.uniform(-0.05, 0.05)) for _ in range(8)]

    def smooth_step(x, a, b):
        k = clamp((x - a) / (b - a))
        return k * k * (3 - 2 * k)

    def reed(x, y):
        if y < 0.62:
            return False
        for rx, top, lean in reeds:
            if y > top:
                t = (y - top) / (1.0 - top)
                if abs(x - (rx + lean * (1 - t) ** 2)) < 0.004 + 0.006 * t:
                    return True
        bank = 1.02 - 0.14 * smooth_step(x, 1.4, 1.75) - 0.12 * smooth_step(x, -0.5, -0.85)
        return y > bank + 0.008 * math.sin(x * 37)

    def air(x, y):
        """Sky, sun and ridges: everything above the water line."""
        dx, dy = x - sx, y - sy
        d = math.hypot(dx, dy)
        near = math.exp(-((x - sx) / 0.45) ** 2)
        for k in (2, 1, 0):
            top, cols, lit = ridges[k]
            h = ridges[k][0](x)
            if y >= h:
                c = pal.path(cols)(clamp(lit * near + 0.35 - (y - h) * 2))
                c = mix(c, pal.rgb("x4"), clamp(1 - (hz - y) / 0.04) * (0.3 + 0.4 * near))
                if y - h < 0.012:
                    c = mix(c, pal.rgb("e9"), 0.7 * near * lit)
                return c, False, "ridge"
        if d <= sr:
            return disc(clamp((d / sr) ** 2.5)), True, "sun"
        ang = math.atan2(dy, dx)
        fan = 0.5 + 0.5 * math.cos(ang * 10 + 0.8 * math.sin(ang * 3))
        ray = fan ** 4 * math.exp(-(d - sr) / 0.6) * 0.5
        glow = math.exp(-((d - sr) / 0.3) ** 2)
        c = sky(clamp(y / hz * 0.7 + glow * 0.55 + 0.05))
        c = mix(c, pal.rgb("e9"), ray)
        halo = math.exp(-((d - sr - 0.012) / 0.03) ** 2)
        c = mix(c, pal.rgb("w9"), halo * 0.85)
        k = clouds(x, y)
        if k:
            cy = y + 0.01 * (1 - k)
            under = clamp(0.25 + near * 0.6 + (cy - 0.2) * 0.8)
            lit = pal.path("a2 x2 x4 e6 e8 e9")(under)
            c = mix(c, lit, clamp(k * 2.2))
            return c, False, "cloud"
        return c, d < sr * 1.3, "sky"

    def field(x, y):
        if reed(x, y):
            rim = not reed(x - 0.008, y) and abs(x - sx) < 0.6 and y < 0.86
            return (pal.rgb("x4") if rim else pal.ground), 1.0, False, "reeds"
        if y < hz:
            c, foc, tag = air(x, y)
            return c, 1.0, foc, tag
        depth = (y - hz) / (1 - hz)
        wob = 0.006 * math.sin(y * 260 + 2 * math.sin(x * 14))
        c, _, tag = air(x + wob, clamp(hz - (y - hz) * 1.3, 0.0, hz - 0.001))
        c = mix(c, pal.rgb("a1"), 0.2 + depth * 0.55)
        width = 0.06 + depth * 0.22
        glint = noise(x * 28, y * 160, 7) > 0.55 - 0.15 * (1 - depth)
        off = abs(x - sx + wob * 2) / width
        if off < 1 and glint:
            c = mix(c, pal.rgb("t9" if off < 0.4 and depth < 0.5 else "e9"), (1 - off ** 2) * (1 - depth * 0.45))
        elif glint and noise(x * 9, y * 40, 2) > 0.62:
            c = mix(c, pal.rgb("e6"), 0.35 * near_sun(x))
        return c, 1.0, False, "lake"

    def near_sun(x):
        return math.exp(-((x - sx) / 0.7) ** 2) + 0.2

    def texts(rows, x_left, cw, unit):
        out = []
        for x, y in ((0.72, 0.17), (0.79, 0.14), (0.85, 0.19), (0.3, 0.11), (1.65, 0.09)):
            out.append((int((x - x_left) / cw), int(y / unit), "v", pal.rgb("x1"), False))
        return out

    return scene("solarized", field, texts, lambda rows: [
        ([(-6.0, hz + 0.002), (2.0, hz + 0.002)], lambda x, y: pal.rgb("e9" if abs(x - sx) < 0.4 else "e6"),
         False, lambda x, y: reed(x, y))],
        inks={"sky": "axew", "cloud": "axew", "sun": "tew", "ridge": "axew", "lake": "axetw"})


# ---------------------------------------------------------------- monokai

CODE_TOKENS = {  # monokai's syntax colours: keywords pink, names green, types cyan, strings yellow, numbers purple
    "e": ["def", "if", "for", "let", "fn", "else", "return", "while", "const", "import", "class", "in", "yield"],
    "g": ["main()", "map", "len", "fold", "push", "init()", "parse", "run()", "zip", "emit"],
    "a": ["int", "str", "self", "None", "true", "void", "u8", "bool", "nil"],
    "w": ['"ok"', "'a'", '"\\n"', '"wpm"', "'{}'", '"key"'],
    "x": ["0x1F", "42", "3.14", "0b101", "1e9", "255", "0xFF", "7"],
    "t": ["{}", "=>", ";", "==", "&&", "[]", "::", "+=", "()", "->", "!=", "||", "<<", "...", "%"],
}


def code(pal):
    """Falling code: lanes of real-looking tokens streaming down in
    monokai's syntax colours (pink keywords, green names, cyan types,
    yellow strings, purple numbers), white-hot heads with long fading
    tails, far lanes dim and sparse, and a pair of huge glowing braces
    where the stream runs thickest."""
    cx = 1.32
    braces = []
    for side in (-1, 1):
        bx = cx + side * 0.27
        tip = bx + side * 0.07
        braces.append(strokes([
            (bezier((bx - side * 0.07, 0.1), (bx, 0.1), (bx, 0.2)), 0.012, 0.022),
            ([(bx, 0.2), (bx, 0.4)], 0.022, 0.022),
            (bezier((bx, 0.4), (bx, 0.48), (tip, 0.49)), 0.022, 0.016),
            (bezier((tip, 0.51), (bx, 0.52), (bx, 0.6)), 0.016, 0.022),
            ([(bx, 0.6), (bx, 0.8)], 0.022, 0.022),
            (bezier((bx, 0.8), (bx, 0.9), (bx - side * 0.07, 0.9)), 0.022, 0.012)]))
    ink = pal.path("e8 e6 e5 x5 x4")

    def cursor(x, y):
        return abs(x - cx) < 0.022 and 0.43 < y < 0.57

    def brace(x, y):
        if cursor(x, y):
            return True
        for b in braces:
            if b(x, y) is not None:
                return True
        return False

    def core(x, y):
        return abs(x - cx) < 0.36 and 0.08 < y < 0.92

    def field(x, y):
        if cursor(x, y):
            return pal.rgb("t9"), 1.0, True, "brace"
        if brace(x, y):
            lit = not brace(x - 0.012, y) or not brace(x, y - 0.012)
            c = mix(ink(y), pal.rgb("t9"), 0.55) if lit else ink(y)
            return c, 1.0, True, "brace"
        glow = math.exp(-((x - cx) / 0.45) ** 2 - ((y - 0.5) / 0.55) ** 2)
        halo = max(math.exp(-((x - cx - s) / 0.07) ** 2) for s in (-0.27, 0.0, 0.27)) * clamp(1 - abs(y - 0.5) * 2.2)
        c = pal.path("- x0 x1 x2 e2 e3")(clamp(glow * 0.7 + halo * 0.4))
        return c, 1.0, core(x, y), "void"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(7)
        out = []
        taken = set()
        kinds = "eeegggaawwxxttt"
        c = 0
        cols = int((1.9 - x_left) / cw)
        while c < cols:
            x = x_left + c * cw
            dense = math.exp(-((x - cx) / 0.6) ** 2)
            depth = rnd.random() * (1 - 0.6 * dense)       # 0 near and bright .. 1 far and dim
            gap = rnd.randint(1, 2)
            if rnd.random() < 0.12 + 0.2 * (1 - dense):
                c += gap + 2
                continue
            head = rnd.uniform(0.25 + 0.3 * dense, 1.2)
            length = rnd.uniform(0.4, 1.0) * (1 - depth * 0.4) + 0.4 * dense
            longest = 6 if rnd.random() < 0.25 else 3
            width = 1
            for r in range(rows):
                y = (r + 0.5) * unit
                t = (head - y) / length                       # 0 at the head, 1 at the end of the tail
                if not 0 <= t <= 1 or rnd.random() < 0.03 + 0.2 * depth:
                    continue
                kind = rnd.choice(kinds)
                tok = rnd.choice([w for w in CODE_TOKENS[kind] if len(w) <= longest] or ["{}"])
                if t < 0.025:
                    tone = "t9" if depth < 0.5 else "t6"
                    kind = "t"
                else:
                    level = (1 - t) ** (1.4 - 0.6 * dense) * (1 - depth * 0.75)
                    tone = kind + str(max(1 + int(dense * 3), min(9, int(1 + level * 9))))
                    if kind == "t":
                        tone = "d" + str(max(2, min(9, int(3 + level * 6))))
                for k, ch in enumerate(tok):
                    xx = x + (k + 0.5) * cw
                    if ch == " " or (r, c + k) in taken or c + k >= cols or any(
                            brace(xx + dx * cw, y + dy * unit) for dx in (-0.5, 0, 0.5) for dy in (-0.4, 0.4)):
                        continue
                    taken.add((r, c + k))
                    out.append((c + k, r, ch, pal.rgb(tone), core(xx, y)))
                width = max(width, len(tok))
            c += width + gap
        return out

    return scene("monokai", field, texts, inks={"brace": "ext"})


# ---------------------------------------------------------------- catppuccin

def cat(pal):
    """A cat sitting on the sill of a round window at night, looking out
    at the moon, its tail curled down, a plant beside it."""
    wx, wy, wr = 1.3, 0.42, 0.34

    def cat_at(x, y):
        bx, by = 1.25, 0.66
        body = ((x - bx) / 0.11) ** 2 + ((y - by) / 0.13) ** 2 <= 1
        head = math.hypot((x - bx - 0.02) / 0.07, (y - 0.5) / 0.065) <= 1
        ears = any(abs(x - ex) < 0.025 * (1 - (0.47 - y) / 0.05) and 0.42 < y < 0.47 for ex in (bx - 0.03, bx + 0.07))
        tail = strokes([(bezier((bx + 0.09, 0.76), (bx + 0.25, 0.8), (bx + 0.2, 0.92)), 0.018, 0.012)])(x, y) is not None
        return body or head or ears or tail

    def field(x, y):
        if cat_at(x, y):
            rim = not cat_at(x + 0.012, y - 0.01)
            return (pal.rgb("a6") if rim else pal.ground), 1.0, True, "cat"
        if 0.79 <= y <= 0.83 and 0.85 < x < 1.8:
            return pal.path("x4 x1")((y - 0.79) * 25), 1.0, True, "sill"
        plant = (1.62 < x < 1.72 and 0.7 < y < 0.79) or (fbm(x * 30, y * 30, 2) > 0.55 and math.hypot(x - 1.67, y - 0.62) < 0.08)
        if plant:
            return (pal.rgb("x4") if y > 0.7 else pal.path("g1 g4 g6")(fbm(x * 40, y * 40))), 1.0, True, "plant"
        d = math.hypot(x - wx, (y - wy) * 1.0)
        if d <= wr:
            mx, my = 1.45, 0.28
            md = math.hypot(x - mx, y - my)
            if md < 0.06:
                return pal.path("t9 w8")(clamp((y - my + 0.06) * 8)), 1.0, True, "moon"
            c = pal.path("d1 a1 a4 e4")(clamp(y * 1.1))
            c = mix(c, pal.rgb("a6"), math.exp(-(md / 0.15) ** 2) * 0.4)
            if abs(x - wx) < 0.006 or abs(y - wy) < 0.006:
                return pal.rgb("x1"), 1.0, True, "frame"
            return c, 1.0, True, "night"
        if d <= wr + 0.025:
            return pal.rgb("x4"), 1.0, True, "frame"
        wall = pal.path("- d1 d4")(clamp(0.5 - d * 0.3 + fbm(x * 8, y * 8) * 0.2))
        return wall, 1.0, False, "wall"

    def texts(rows, x_left, cw, unit):
        out = []
        rnd = random.Random(3)
        for _ in range(rows * 2):
            x, y = rnd.uniform(1.0, 1.6), rnd.uniform(0.1, 0.7)
            if field(x, y)[3] == "night":
                out.append((int((x - x_left) / cw), int(y / unit), rnd.choice(".·*'"), pal.rgb("t9"), True))
        return out

    return scene("catppuccin", field, texts)


# ---------------------------------------------------------------- rose pine

def petal_at(petals, x, y):
    """The first petal (front to back) holding (x, y): (index, u, v, q) in
    its own frame (q 0 at its middle, 1 at its wavy edge), or None."""
    for i, (px, py, rx, ry, rot, wave) in enumerate(petals):
        dx, dy = x - px, y - py
        c, s = math.cos(rot), math.sin(rot)
        u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
        a = math.atan2(v, u)
        edge = 1 + 0.07 * math.sin(a * 3 + wave) + 0.05 * math.sin(a * 7 + wave * 2)
        if v < 0:
            edge += 0.06 * math.exp(-((a + math.pi / 2) / 0.35) ** 2)     # a curled tip on top
        q = math.hypot(u, v) / edge
        if q <= 1:
            return i, u, v, q
    return None


def rose(pal):
    """A single red-pink rose, realistic: a cup of overlapping petals,
    each shaded from a deep base to a lit, rolled-back lip, dark crevices
    between them and a tight spiral bud at the heart; green sepals, a
    thorny stem and two veined leaves; soft bokeh and gold dust behind."""
    cx, cy = 1.3, 0.36
    petals = [  # front to back: (x, y, rx, ry, tilt, wave)
        (cx + 0.01, cy + 0.13, 0.12, 0.11, 0.0, 0.4),        # the front petal
        (cx - 0.09, cy + 0.09, 0.11, 0.12, -0.35, 1.3),
        (cx + 0.1, cy + 0.08, 0.11, 0.12, 0.35, 2.1),
        (cx - 0.17, cy + 0.03, 0.09, 0.12, -0.6, 0.9),       # outer petals flaring out
        (cx + 0.18, cy + 0.02, 0.09, 0.12, 0.6, 2.7),
        (cx - 0.015, cy - 0.09, 0.05, 0.05, -0.3, 0.2),      # the bud at the heart
        (cx + 0.03, cy - 0.1, 0.055, 0.05, 0.4, 1.7),
        (cx - 0.06, cy - 0.06, 0.08, 0.1, -0.2, 3.1),        # inner cup walls
        (cx + 0.07, cy - 0.07, 0.08, 0.1, 0.25, 0.6),
        (cx, cy - 0.13, 0.11, 0.08, 0.0, 1.1),               # the back petals
        (cx - 0.13, cy - 0.07, 0.1, 0.13, -0.4, 2.4),
        (cx + 0.13, cy - 0.08, 0.1, 0.13, 0.4, 0.3)]
    shade = pal.path("- x0 e1 e2 e3 e5 e6 e7 e8 e9")
    base = (cx, cy + 0.23)
    spine = bezier(base, (cx + 0.07, 0.68), (cx - 0.02, 1.04), 24)
    stem = strokes([(spine, 0.013, 0.011)])
    calyx = (cx, cy + 0.15)
    sepals = strokes([(bezier(calyx, (cx + dx * 0.7, calyx[1] + dy * 0.35), (cx + dx, calyx[1] + dy), 10),
                       0.034, 0.004) for dx, dy in ((-0.2, 0.15), (-0.1, 0.18), (0.11, 0.18), (0.21, 0.14))])
    thorns = [(spine[k][0] + 0.01 * side, spine[k][1], side) for k, side in ((7, 1), (12, -1), (19, 1))]
    leaves = [(cx + 0.045, 0.75, -0.35, 0.2, 0.06), (cx + 0.02, 0.87, math.pi + 0.45, 0.17, 0.05)]

    def leaf(x, y):
        for lx, ly, ang, ln, wd in leaves:
            dx, dy = x - lx, y - ly
            s = (dx * math.cos(ang) + dy * math.sin(ang)) / ln
            w = (-dx * math.sin(ang) + dy * math.cos(ang))
            if 0 < s < 1:
                half = wd * math.sin(math.pi * s ** 0.8) ** 0.9 * (1 + 0.1 * math.sin(s * 45))
                if abs(w) < half:
                    return s, w / half
        return None

    def thorn(x, y):
        for tx, ty, side in thorns:
            u, v = (x - tx) * side, ty - y
            if 0 < u < 0.045 and abs(v - u * 0.6) < 0.016 * (1 - u / 0.045):
                return True
        return False

    def field(x, y):
        hit = petal_at(petals, x, y)
        if hit:
            i, u, v, q = hit
            front, inner = i < 5, 5 <= i < 9
            t = 0.42 + 0.07 * math.sin(i * 2.3) - 0.25 * u * (0.5 if front else -0.3) - 0.2 * v
            t += 0.25 * (q - 0.6) if v < 0 else -0.25 * q * (v if front else 1)
            lip = 0.8 if 3 <= i < 5 or i >= 9 else 0.86
            if v < 0 and q > lip:
                t = 0.78 + 0.22 * (q - lip) / (1 - lip)                    # the rolled, lit lip
            elif v < 0 and q > lip - 0.08:
                t -= 0.3                                               # shadow under the lip
            if front and v > 0:
                t -= 0.4 * v ** 1.5                                     # the underside, in shadow
            if inner:
                t -= 0.15
            if i == 5 or i == 6:
                spiral = (math.atan2(v, u) / (2 * math.pi) + q * 1.6) % 1
                t = 0.5 + 0.3 * q - (0.4 if spiral < 0.18 else 0)
            behind = petal_at(petals[:i], x, y + 0.028)
            if behind and i >= 3:
                t -= 0.45 if behind[0] < 5 else 0.3                    # a crevice above a petal in front
            return shade(clamp(t, 0.08)), 1.0, True, "rose"
        if ((x - cx) / 0.035) ** 2 + ((y - base[1] - 0.025) / 0.03) ** 2 < 1:
            return pal.path("g4 g2 g1")(clamp((x - cx + 0.03) * 12)), 1.0, True, "stem"
        s = sepals(x, y)
        if s is not None:
            return pal.path("g2 g4 g5")(s), 1.0, True, "stem"
        if stem(x, y) is not None or thorn(x, y):
            lit = stem(x - 0.008, y) is None and not thorn(x - 0.008, y)
            return pal.rgb("g4" if lit else "g1"), 1.0, True, "stem"
        lf = leaf(x, y)
        if lf:
            s, w = lf
            vein = abs(w) < 0.1 or (s * 9 - abs(w) * 1.4) % 1 < 0.14
            c = pal.path("d1 g1 g2 g4 g5")(clamp(0.35 + 0.35 * (w < 0) + 0.2 * (1 - s) - 0.15 * abs(w) ** 3))
            return (mix(c, pal.rgb("d1"), 0.55) if vein else c), 1.0, True, "leaf"
        glow = math.exp(-((x - cx) / 0.55) ** 2 - ((y - cy) / 0.5) ** 2)
        c = pal.path("- d0 x0 d2 x2")(glow * 0.75)
        for bx, by, br, col in ((0.75, 0.25, 0.08, "x3"), (0.55, 0.62, 0.11, "d3"), (1.78, 0.18, 0.07, "w3"),
                                (1.75, 0.75, 0.09, "x2"), (0.2, 0.4, 0.1, "d2"), (-0.4, 0.2, 0.08, "x2"),
                                (0.95, 0.85, 0.06, "w2"), (-0.7, 0.7, 0.12, "d2")):
            k = math.hypot(x - bx, y - by) / br
            if k < 1:
                c = mix(c, pal.rgb(col), 0.55 * (1 - k ** 6))
        return c, 1.0, False, "dark"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(15)
        out = []
        for _ in range(rows * 3):
            x, y = rnd.uniform(-3, 1.9), rnd.uniform(0.0, 1.0)
            if field(x, y)[3] == "dark":
                out.append((int((x - x_left) / cw), int(y / unit), rnd.choice(".·'"),
                            rnd.choice([pal.rgb("w6"), pal.rgb("w8"), pal.rgb("e8")]), False))
        return out

    return scene("rose pine", field, texts, inks={"rose": "ex", "dark": "dxw", "leaf": "dg", "stem": "dg"})



MORE = {"jungle": jungle, "blossom": blossom, "lavender": lavender, "snowpeaks": snowpeaks,
        "reef": reef, "volcano": volcano, "bamboo": bamboo, "bat": bat, "mountains": mountains,
        "coffee": coffee, "sun": sun, "code": code, "cat": cat, "rose": rose}
