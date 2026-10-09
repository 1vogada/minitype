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

def _massif(peaks, jag=0.012, seed=0, power=1.5):
    """A mountain line: peaks (x, half width, height[, power]) above the
    shore; a power over 1 gives concave flanks that flare out into a foot.
    height(x) gives (height, x of the peak it belongs to, its height)."""
    def height(x):
        best = (0.0, peaks[0][0], peaks[0][2])
        for cx, w, ht, *pw in peaks:
            h = ht * max(0.0, 1 - abs(x - cx) / w) ** (pw[0] if pw else power)
            if h > best[0]:
                best = (h, cx, ht)
        h = best[0]
        if h > 0:
            h += jag * (fbm(x * 22, 0.5, seed) - 0.5) * min(1.0, h * 8)
        return max(0.0, h), best[1], best[2]
    return height


def mountains(pal):
    """Arctic dusk: a great snowy massif, one broad face lit pink and the
    other in blue shadow, ribs and couloirs running down from the summit,
    scree fans and a pine treeline at its foot dissolving in mist, ranges
    stepping back into cold haze, and a still fjord mirroring it all,
    with a cabin's lit window on the shore."""
    shore = 0.765
    sky = pal.path("d0 d1 d4 a1 a4 a6")
    sx, sy = 1.33, shore - 0.6                  # the summit
    main = _massif([(sx, 0.62, 0.6, 1.1),                    # the peak
                    (1.68, 0.42, 0.4, 1.15), (1.02, 0.4, 0.34, 1.15),   # its shoulders
                    (sx, 1.1, 0.2, 2.2), (0.7, 0.3, 0.12)], jag=0.04, seed=3)   # the foot
    hills = _massif([(0.56, 0.24, 0.065), (0.92, 0.2, 0.085), (0.2, 0.3, 0.05), (1.6, 0.16, 0.075),
                     (1.95, 0.3, 0.11), (-0.3, 0.3, 0.06), (-0.9, 0.35, 0.05), (-1.6, 0.4, 0.06),
                     (-2.4, 0.4, 0.05)], jag=0.0, seed=8, power=0.7)
    far = ridge([(0.2, 0.6, 0.2), (0.95, 0.45, 0.22), (-1.0, 0.7, 0.22), (-2.3, 0.6, 0.2)], 0.57)
    near = ridge([(0.6, 0.5, 0.15), (-0.4, 0.6, 0.18), (-1.7, 0.6, 0.16), (-2.7, 0.5, 0.15)], 0.66)
    rnd = random.Random(7)
    trees = {}
    for _ in range(520):                        # pines along the shore and up the foothills
        tx = rnd.uniform(-3.2, 1.95)
        th = rnd.uniform(0.03, 0.07)
        lift = rnd.random() ** 1.5 * 0.1
        trees.setdefault(int(tx * 30), []).append((tx, lift, th))
    snow_lit = pal.path("a4 a6 t5 t7 t9")
    snow_dark = pal.path("d1 a1 a4 a6")
    rock = pal.path("- d0 d1 d4 d6")
    water = pal.path("a1 d1 d0 -")
    cabin_x = 0.98

    def tree_at(x, y, ground_y):
        """A pine standing on ground_y near x: its light 0..1, or None."""
        k = int(x * 30)
        for kk in (k - 1, k, k + 1):
            for tx, lift, th in trees.get(kk, ()):
                if abs(x - cabin_x) < 0.07 and lift < 0.03:
                    continue                    # a clearing for the cabin
                base = ground_y - lift * 0.5 + 0.004
                t = (base - y) / th
                if 0 <= t <= 1:
                    tier = (t * 4) % 1.0
                    half = th * 0.42 * (1 - t) * (0.6 + 0.4 * (1 - tier))
                    if abs(x - tx) <= max(half, 0.004):
                        return clamp(0.5 - (x - tx) / (half + 0.004) * 0.5)
        return None

    def land(x, y):
        """Colour, focus and tag above the shore."""
        hh, _, _ = hills(x)
        mh, _, _ = main(x)
        mist = math.exp(-((y - 0.7 - 0.015 * math.sin(x * 5)) / 0.04) ** 2) * (0.25 + 0.5 * fbm(x * 4, y * 9, 5))
        ground = shore - hh
        t = tree_at(x, y, ground)             # pines in front of everything low down
        if t is not None:
            c = pal.path("- d0 g0 g2 a4")(t * 0.85)
            return mix(c, pal.rgb("a4"), mist * 0.4), False, "trees"
        if y >= ground:                         # forested foothills, in front of the peak
            depth = (y - ground) / max(hh, 0.02)
            c = pal.path("- d0 g0")(clamp(0.55 - depth * 0.4 + fbm(x * 60, y * 90, 4) * 0.35))
            return mix(c, pal.rgb("a6"), mist), False, "trees"
        top = shore - mh
        if y >= top and mh > 0:
            d = y - top
            el = clamp((shore - y) / 0.6)      # 1 at the summit
            fan = (x - sx) / (y - sy + 0.05)   # rays down from the summit
            rib = fbm(fan * 3.0 + 7, y * 2.5, 11)
            spine = sx + (y - sy) * 0.3 + (rib - 0.5) * 0.06
            lit = x < spine
            # one broad lit face, brightest by the spine, ribs streaking it
            face = clamp(1 - abs(x - spine) / 0.5)
            shade = (rib - 0.5) * 0.7 + (face - 0.5) * 0.35 - d * 0.6
            gully = fbm(fan * 7 + 3, y * 5, 2) + (fbm(x * 50, y * 30, 6) - 0.5) * 0.25
            cone = clamp(1 - abs(gully - 0.45) * 4)
            talus = clamp((0.3 + cone * 0.22 - el) * 7 + (fbm(x * 20, y * 8, 12) - 0.5) * 1.5)
            if talus > 0.5:                    # scree fans spreading out below the cliffs
                grit = noise(x * 160, y * 300, 9)
                c = rock(clamp((0.6 if lit else 0.36) + (grit - 0.5) * 0.8 + cone * 0.25 + shade * 0.3))
                c = mix(c, pal.rgb("a4"), clamp((y - 0.6) * 5) * 0.45)   # haze at the foot
            elif gully > 0.3 + el * 0.45 + clamp(0.02 - d) * 12 * el * el - clamp(0.42 - el) * 3:
                c = rock(clamp((0.55 if lit else 0.14) + shade * 1.1 + (fbm(x * 80, y * 140, 4) - 0.5) * 0.5))
                c = mix(c, pal.rgb("a1"), clamp((y - 0.45) * 3) * 0.6)  # bluer, hazier lower down
            elif lit:
                c = snow_lit(clamp(0.56 + shade * 1.3 + (fbm(fan * 12, y * 6, 14) - 0.5) * 0.7))
                c = mix(c, pal.rgb("e9"), clamp(el * 1.7 - 0.95) * 0.6)   # alpenglow
            else:
                c = snow_dark(clamp(0.72 + shade * 0.8 + (fbm(fan * 12, y * 6, 14) - 0.5) * 0.5))
            return mix(c, pal.rgb("a6"), mist), abs(x - sx) < 0.62 and y < 0.68, "peak"
        for k, (layer, col) in enumerate(((near, "a1 d4 d1 d0"), (far, "a6 a4 a1 d4"))):
            ly = layer(x)
            if y >= ly:
                streak = fbm(x * 30 + (y - ly) * 20, y * 3, 13 + k)
                c = pal.path(col)(clamp((y - ly) * 4 - (streak - 0.5) * 0.25 * (1 - k * 0.5)))
                haze = clamp((y - 0.58) * 6) * 0.45
                return mix(mix(c, pal.rgb("a6"), haze), pal.rgb("a6"), mist), False, "range"
        return sky(clamp((y / 0.66) ** 1.3)), False, "sky"

    def field(x, y):
        if y >= shore:
            if y < shore + 0.006:              # the waterline: pebbles and a glint
                return pal.path("- d0 d4 t5")(noise(x * 90, 1, 3) * 0.9), 1.0, False, "fjord"
            dy = y - shore
            my = shore - dy * 1.9
            # a soft mirror: two samples a little apart, blended
            c1, _, _ = land(x, clamp(my, 0.0, shore - 0.001))
            c2, _, _ = land(x + 0.01, clamp(my - 0.025, 0.0, shore - 0.001))
            c = mix(c1, c2, 0.5)
            calm = clamp((x - 0.7) * 2.5)       # under the peak the mirror is sharper
            c = mix(c, water(clamp(dy * 3)), 0.35 + 0.3 * (1 - calm))
            c = mix(c, pal.ground, clamp(0.1 + dy * 1.4))
            if abs(x - cabin_x - 0.012) < 0.014 * (1 + dy * 3) and noise(x * 40, y * 120) > 0.35:
                c = mix(c, pal.rgb("w6"), clamp(0.75 - dy * 5))
            ripple = math.sin(y * 420 + math.sin(x * 9) * 2) * 0.5 + 0.5
            if calm > 0.5 and ripple > 0.95 and noise(x * 5, y * 40, 6) > 0.6:
                c = mix(c, pal.rgb("a6"), 0.3)
            return c, 1.0, False, "fjord"
        dx = x - cabin_x
        if abs(dx) < 0.07 and shore - 0.12 < y:         # a log cabin with a snowy gable roof
            eave = shore - 0.055
            roof = eave - (0.065 - abs(dx)) * 0.9
            if y >= roof and abs(dx) < 0.065:
                if y < eave and y < roof + 0.022:
                    return pal.path("a4 t6 t8")(clamp(0.9 - dx * 8)), 1.0, False, "cabin"   # snow
                if y < eave:
                    return pal.rgb("x1"), 1.0, False, "cabin"      # the gable
                if abs(dx) < 0.052:
                    win = abs(dx - 0.018) < 0.012 and shore - 0.042 < y < shore - 0.016
                    door = abs(dx + 0.022) < 0.009 and y > shore - 0.04
                    if win:
                        return pal.rgb("w7"), 1.0, False, "cabin"
                    if door:
                        return pal.rgb("d0"), 1.0, False, "cabin"
                    log = (y * 160) % 1.0 < 0.3
                    return pal.rgb("x0" if log else "x2"), 1.0, False, "cabin"
            if 0.03 < dx < 0.045 and roof - 0.03 < y < roof + 0.01:   # chimney
                return pal.rgb("d1"), 1.0, False, "cabin"
        c, foc, tag = land(x, y)
        return c, 1.0, foc, tag

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 5, 0.3, [pal.rgb("t8"), pal.rgb("a8")], 23,
                     chars="..·'")

    return scene("nord", field, texts, inks={"sky": "dat", "peak": "date", "range": "dat",
                                             "trees": "dga", "fjord": "dat w", "cabin": "dxwta"})


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
    """The sun up close: a blazing disc with a granulated face, flares
    looping off its edge and rays fanning out over a deep blue."""
    sx, sy, sr = 1.3, 0.5, 0.33
    face = pal.path("e1 e4 e6 w6 w9")
    light = sphere_light(sx, sy, sr, -0.2, -0.3)
    flares = strokes([(bezier((sx + sr * math.cos(a), sy - sr * math.sin(a)),
                              (sx + (sr + 0.16) * math.cos(a + 0.15), sy - (sr + 0.16) * math.sin(a + 0.15) * 1),
                              (sx + sr * math.cos(a + 0.3), sy - sr * math.sin(a + 0.3))), 0.012, 0.008)
                      for a in (0.6, 1.9, 2.8, 4.0)])

    def field(x, y):
        d = math.hypot(x - sx, y - sy)
        if d <= sr:
            g = fbm(x * 40, y * 40, 3)
            return face(clamp(light(x, y) * 0.8 + g * 0.3 - 0.05)), 1.0, True, "sun"
        if flares(x, y) is not None:
            return pal.rgb("w6"), 1.0, True, "flare"
        ang = math.atan2(y - sy, x - sx)
        ray = clamp(math.cos(ang * 12) * 0.5 + 0.5) ** 3 * math.exp(-((d - sr) / 0.5))
        corona = math.exp(-((d - sr) / 0.08) ** 2)
        c = pal.path("- a1 a4")(clamp(0.3 + y * 0.5 - 0.2))
        c = mix(c, pal.rgb("e6"), corona * 0.8)
        c = mix(c, pal.rgb("w6"), ray * 0.45)
        return c, 1.0, False, "space"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 6, 1.0, [pal.rgb("t8"), pal.rgb("a8")], 41)

    return scene("solarized", field, texts, inks={"space": "aew", "sun": "ew"})


# ---------------------------------------------------------------- monokai

def code(pal):
    """An editor window floating in the dark: title bar with three dots,
    line numbers and syntax-coloured code, a glow under it."""
    x0, y0, x1, y1 = 0.62, 0.12, 1.88, 0.9
    lines_of_code = [
        [("def ", "e"), ("type_fast", "g"), ("(", "t"), ("words", "w"), ("):", "t")],
        [("    ", "t"), ("for ", "e"), ("w ", "t"), ("in ", "e"), ("words", "w"), (":", "t")],
        [("        ", "t"), ("if ", "e"), ("w", "t"), (" == ", "e"), ('"wow"', "w")],
        [("            ", "t"), ("yield ", "e"), ("speed", "a"), ("(w)", "t")],
        [("    ", "t"), ("return ", "e"), ("None", "x")],
        [("", "t")],
        [("# ", "d"), ("faster every day", "d")],
        [("streak ", "t"), ("= ", "e"), ("42", "x")],
    ]

    def field(x, y):
        if x0 <= x <= x1 and y0 <= y <= y1:
            if y < y0 + 0.07:
                return pal.path("d1 d4")(0.3), 1.0, True, "window"
            if x < x0 + 0.11:
                return pal.path("- d1")(0.6), 1.0, True, "window"
            return pal.path("- d1")(0.25), 1.0, True, "window"
        glow = math.exp(-((x - 1.25) / 0.8) ** 2 - ((y - 0.95) / 0.12) ** 2)
        grid = (abs(math.sin(x * 25)) < 0.05 or abs(math.sin(y * 25)) < 0.05) and y > 0.6
        c = pal.path("d1 x1 a1")(glow * 0.9)
        if grid:
            c = mix(c, pal.rgb("x4"), 0.35 * (y - 0.6) * 2.5)
        return c, 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        out = []
        col0 = lambda x: int((x - x_left) / cw)
        r0 = int((y0 + 0.03) / unit)
        for k, (cx_, col) in enumerate(((x0 + 0.03, "e6"), (x0 + 0.06, "w6"), (x0 + 0.09, "g6"))):
            out.append((col0(cx_), r0, "o", pal.rgb(col), True))
        first = int((y0 + 0.1) / unit)
        for i, segs in enumerate(lines_of_code):
            r = first + i * max(1, rows // 22)
            if (r + 1) * unit > y1:
                break
            out.append((col0(x0 + 0.02), r, str(i + 1), pal.rgb("d6"), True))
            c = col0(x0 + 0.13)
            for text, colour in segs:
                for chh in text:
                    if chh != " ":
                        out.append((c, r, chh, pal.rgb(colour + ("6" if colour != "d" else "6")), True))
                    c += 1
        out.append((c + 1, first + (len(lines_of_code) - 1) * max(1, rows // 22), "_", pal.rgb("t9"), True))
        return out

    return scene("monokai", field, texts, inks={"window": "d", "room": "dxa"})


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

def rose(pal):
    """A single rose: spiralling petals deepening to the heart, a stem
    with thorns and two leaves, gold dust in a soft dark glow."""
    cx, cy, r = 1.3, 0.36, 0.2
    stem = strokes([(bezier((cx, cy + 0.15), (cx + 0.05, 0.65), (cx - 0.02, 0.98)), 0.012, 0.01)])
    leaves = [(cx + 0.02, 0.62, 1), (cx - 0.01, 0.78, -1)]

    def petal(x, y):
        u, v = (x - cx) / r, (y - cy) / (r * 0.8)
        d, a = math.hypot(u, v), math.atan2(v, u)
        edge = 0.85 + 0.15 * math.cos(a * 5)
        if d > edge or (v > 0.55 and abs(u) < 0.55 - (v - 0.55)):
            return None
        spiral = (a / (2 * math.pi) + d * 2.2) % 1
        return d, spiral, u, v

    def field(x, y):
        p = petal(x, y)
        if p:
            d, spiral, u, v = p
            light = clamp(0.55 + (1 - d) * 0.15 - u * 0.2 - v * 0.25 - (0.35 if spiral < 0.12 else 0) - (0.3 if d < 0.2 else 0))
            return pal.path("x1 e1 e4 e6 e8")(light), 1.0, True, "rose"
        if stem(x, y) is not None:
            return pal.rgb("g4"), 1.0, True, "stem"
        for lx, ly, side in leaves:
            u, v = (x - lx) * side, y - ly
            if 0 < u < 0.15 and abs(v + u * 0.4) < 0.045 * math.sin(math.pi * u / 0.15):
                return pal.path("d1 g4 g6")(clamp(0.6 - abs(v + u * 0.4) * 10)), 1.0, True, "leaf"
        glow = math.exp(-((x - cx) / 0.6) ** 2 - ((y - cy) / 0.45) ** 2)
        return pal.path("- d1 x1 e1")(glow * 0.7), 1.0, False, "dark"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(15)
        out = []
        for _ in range(rows * 2):
            x, y = rnd.uniform(-3, 1.9), rnd.uniform(0.0, 1.0)
            if field(x, y)[3] == "dark":
                out.append((int((x - x_left) / cw), int(y / unit), rnd.choice(".·'"),
                            rnd.choice([pal.rgb("w6"), pal.rgb("w8")]), False))
        return out

    return scene("rose pine", field, texts, inks={"rose": "ex", "dark": "dxe"})


MORE = {"jungle": jungle, "blossom": blossom, "lavender": lavender, "snowpeaks": snowpeaks,
        "reef": reef, "volcano": volcano, "bamboo": bamboo, "bat": bat, "mountains": mountains,
        "coffee": coffee, "sun": sun, "code": code, "cat": cat, "rose": rose}
