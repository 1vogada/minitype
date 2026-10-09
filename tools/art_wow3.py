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

def limbs(paths, cell=0.05):
    """Thick polylines like strokes(), bucketed on a grid so hundreds of
    them stay fast: paths [(points, width at start, width at end)];
    inside(x, y) -> (t along, nx, ny, path index) for the thickest one
    there (nx, ny: offset from its axis over its radius, for round
    shading), or None."""
    grid = {}
    for k, (pts, w0, w1) in enumerate(paths):
        n = len(pts) - 1
        for j, (a, b) in enumerate(zip(pts, pts[1:])):
            ra, rb = w0 + (w1 - w0) * j / n, w0 + (w1 - w0) * (j + 1) / n
            seg = (a[0], a[1], b[0] - a[0], b[1] - a[1], ra, rb, j / n, 1 / n, k)
            r = max(ra, rb)
            for gx in range(math.floor((min(a[0], b[0]) - r) / cell), math.floor((max(a[0], b[0]) + r) / cell) + 1):
                for gy in range(math.floor((min(a[1], b[1]) - r) / cell),
                                math.floor((max(a[1], b[1]) + r) / cell) + 1):
                    grid.setdefault((gx, gy), []).append(seg)

    def inside(x, y):
        best = None
        for ax, ay, dx, dy, ra, rb, t0, dt, k in grid.get((math.floor(x / cell), math.floor(y / cell)), ()):
            u = clamp(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy or 1e-9))
            r = ra + (rb - ra) * u
            px, py = x - ax - dx * u, y - ay - dy * u
            if px * px + py * py <= r * r and (best is None or r > best[0]):
                best = (r, t0 + dt * u, px / r, py / r, k)
        return best and best[1:]
    return inside


def round_light(nx, ny, lx=-0.6, ly=-0.5):
    """0..1 light on a round limb or ball at offset (nx, ny) from its axis."""
    z = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
    return clamp(nx * lx + ny * ly + z * math.sqrt(max(0.0, 1 - lx * lx - ly * ly)))


def jungle(pal):
    """A waterfall dropping through the jungle into a misty pool: huge
    leaves in front, buttressed trunks fading into the mist behind,
    hanging vines and lianas everywhere, magenta flowers."""
    fx = 1.0
    sky = pal.path("d4 a4 t4")
    leaves = []
    for cx, cy, ang, ln in ((1.55, 0.55, -40, 0.42), (1.75, 0.35, -75, 0.36), (1.4, 0.8, -15, 0.38),
                            (1.85, 0.75, -110, 0.3), (0.62, 0.86, -160, 0.32)):
        a = math.radians(ang)
        leaves.append((cx, cy, math.cos(a), math.sin(a), ln))

    # trees in three depths: (x, width, lean); near ones get buttress roots
    rnd = random.Random(23)
    near = [(-0.55, 0.07, 0.04), (0.4, 0.05, -0.03), (1.6, 0.055, 0.05), (-1.95, 0.075, -0.05),
            (-2.75, 0.055, 0.03)]
    mid = [(x, rnd.uniform(0.022, 0.03), rnd.uniform(-0.06, 0.06))
           for x in (-0.82, -0.18, 0.12, 0.62, 1.4, 1.86, -1.35, -1.62, -2.3, -2.95)]
    far = [(rnd.uniform(-3.2, 1.9), rnd.uniform(0.01, 0.016), rnd.uniform(-0.04, 0.04)) for _ in range(30)]
    far = [t for t in far if abs(t[0] - fx) > 0.32]

    def trunks(spec, base, roots):
        paths = []
        for x, w, lean in spec:
            paths.append((bezier((x, base), (x + lean * 0.3, 0.4), (x + lean, -0.06), 10), w, w * 0.75))
            for side in ((-1, 1) if roots else ()):
                for k in (0.9, 1.7):
                    paths.append((bezier((x, base - 0.2 * k / 1.7), (x + side * w * k * 0.9, base - 0.04),
                                         (x + side * w * k * 1.6, base + 0.015), 6), w * 0.35, w * 0.2))
        return limbs(paths)
    near_t = trunks(near, 0.86, True)
    mid_t = trunks(mid, 0.8, True)
    far_t = trunks(far, 0.76, False)

    # vines hang from the canopy, some leafy; lianas loop between trunks
    vpaths, vleaf = [], []
    vr = random.Random(5)
    for _ in range(34):
        x = vr.uniform(-3.2, 1.9)
        if abs(x - fx) < 0.14:
            continue
        ln, sway = vr.uniform(0.18, 0.72), vr.uniform(-0.07, 0.07)
        pts = bezier((x, -0.05), (x + sway * 1.6, ln * 0.45), (x + sway, ln), 14)
        vpaths.append((pts, 0.0065, 0.0045))
        if vr.random() < 0.6:                                  # leaves along it, alternating sides
            side = 1
            for p in pts[2:-1:2]:
                ang = math.radians(90 - side * 50 + vr.uniform(-15, 15))
                ll = vr.uniform(0.045, 0.065)
                vleaf.append(([p, (p[0] + math.cos(ang) * ll * side * 0.9, p[1] + math.sin(ang) * ll * 0.6)],
                              0.017, 0.003))
                side = -side
    for (x1, y1), (x2, y2), sag in (((-0.55, 0.12), (0.4, 0.2), 0.3), ((0.4, 0.3), (0.62, 0.15), 0.14),
                                    ((1.6, 0.1), (1.86, 0.2), 0.2), ((-1.95, 0.15), (-0.55, 0.32), 0.3),
                                    ((-2.75, 0.25), (-1.95, 0.1), 0.28), ((-0.82, 0.4), (-0.18, 0.3), 0.18)):
        vpaths.append((bezier((x1, y1), ((x1 + x2) / 2, max(y1, y2) + sag), (x2, y2), 18), 0.006, 0.006))
    nv = len(vpaths)
    vines = limbs(vpaths + vleaf)

    bark = pal.path("- d0 d1 w0 w1 w3")
    moss = pal.path("d1 d4 g1 g4")
    mid_bark = pal.path("- d0 d1 a1 a2")
    far_bark = pal.path("a1 a2 a3 t2")

    def leaf_at(x, y):
        for cx, cy, dx, dy, ln in leaves:
            u = (x - cx) * dx + (y - cy) * dy * 2
            v = -(x - cx) * dy + (y - cy) * dx * 2 * 0.5
            if 0 <= u <= ln:
                half = ln * 0.32 * math.sin(math.pi * u / ln) ** 0.8
                if abs(v) <= half and not (abs(v) > half * 0.35 and math.sin(u * 60) > 0.75):
                    return u / ln, v / (half or 1)
        return None

    def trunk_colour(hit, x, y, path, mossy):
        t, nx, ny, k = hit
        light = round_light(nx, ny)
        grain = noise(nx * 5 + k * 7.3, y * 14, k) - 0.5
        if mossy and math.sin(y * 70 + nx * 2.5 + k * 3) > 0.86:          # a creeper wound round it
            return pal.path("d1 d4 g1 g4")(light), 1.0, False, "vine"
        if mossy and fbm(x * 22, y * 16, k + 3) > 0.6 - (y - 0.4) * 0.25:
            return moss(clamp(light * 0.8 + grain * 0.4)), 1.0, False, "trunk"
        return path(clamp(light * 0.85 + grain * 0.6)), 1.0, False, "trunk"

    def field(x, y):
        lf = leaf_at(x, y)
        if lf:
            u, v = lf
            c = pal.path("d1 g1 a4 g4 g6")(clamp(0.45 + v * 0.3 + (1 - u) * 0.2))
            if abs(v) < 0.08:
                c = pal.rgb("t4")                              # the midrib
            return c, 1.0, True, "leaf"
        hit = vines(x, y)
        if hit:
            t, nx, ny, k = hit
            if k < nv:
                return pal.path("- d1 d4 g1")(round_light(nx, ny) * 0.9), 1.0, False, "vine"
            return pal.path("d4 g1 g4 a6")(clamp(round_light(nx, ny) * 0.7 + t * 0.4)), 1.0, False, "vine"
        if abs(x - fx - 0.02 * math.sin(y * 9)) < 0.09 and 0.16 < y < 0.8:
            streak = math.sin(x * 260 + y * 30) * 0.5 + 0.5
            return pal.path("a4 t4 t6 t9")(clamp(0.5 + streak * 0.5 - abs(x - fx) * 3)), 1.0, True, "fall"
        hit = near_t(x, y)
        if hit:
            return trunk_colour(hit, x, y, bark, True)
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
        hit = mid_t(x, y)
        if hit:
            return trunk_colour(hit, x, y, mid_bark, False)
        mist = math.exp(-((y - 0.7) / 0.15) ** 2)
        mist += clamp(math.sin((x * 0.6 + y * 0.35) * 8) * 0.5 + 0.5) ** 6 * (1 - y) * 0.9   # sun shafts
        back = fbm(x * 5, y * 7, 9, 3)
        if back > 0.56 + y * 0.3:                               # far canopy, in the haze
            c = pal.path("d4 a1 a2 a4")(clamp((back - 0.5) * 3 + (1 - y) * 0.3))
            return mix(c, pal.rgb("t6"), mist * 0.3), 1.0, False, "haze"
        hit = far_t(x, y)
        if hit:
            t, nx, ny, k = hit
            c = far_bark(clamp(0.2 + round_light(nx, ny) * 0.6 + y * 0.3))
            return mix(c, pal.rgb("t6"), mist * 0.5), 1.0, False, "haze"
        return mix(sky(clamp(y * 1.2)), pal.rgb("t6"), clamp(mist * 0.45)), 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd2 = random.Random(31)
        out = []
        for _ in range(rows * 2):
            x, y = rnd2.uniform(-3.0, 1.9), rnd2.uniform(0.2, 0.9)
            if field(x, y)[3] == "canopy":
                out.append((int((x - x_left) / cw), int(y / unit), rnd2.choice("*@"),
                            rnd2.choice([pal.rgb("e6"), pal.rgb("e8"), pal.rgb("w8")]), False))
        return out

    return scene("jungle", field, texts)


# ---------------------------------------------------------------- cherry blossom

def grow(rnd, p, ang, length, width, depth, paths, tips, spread=38, lo=-172, hi=-8, kids=(2, 3)):
    """A branching limb from p at angle ang (degrees, -90 is up), each
    piece a gently bent curve; adds (points, w0, w1) to paths and
    (x, y, depth) to tips at every fork and branch end."""
    a = math.radians(ang)
    end = (p[0] + math.cos(a) * length, p[1] + math.sin(a) * length)
    bend = rnd.uniform(-0.4, 0.4) * length
    ctrl = ((p[0] + end[0]) / 2 - math.sin(a) * bend, (p[1] + end[1]) / 2 + math.cos(a) * bend)
    w1 = width * 0.68
    phase, kink = rnd.uniform(0, 6.3), rnd.uniform(0.04, 0.09) * length
    pts = [(px - math.sin(a) * kink * math.sin(phase + j * 1.9) * (j % 6 > 0), py + math.cos(a) * kink * math.sin(phase + j * 1.9) * (j % 6 > 0))
           for j, (px, py) in enumerate(bezier(p, ctrl, end, 6))]
    paths.append((pts, width, w1))
    tips.append((end[0], end[1], depth))
    if depth == 0:
        return
    n = rnd.choice(kids)
    for j in range(n):
        side = (j - (n - 1) / 2) / max(1, (n - 1) / 2)
        a2 = max(lo, min(hi, ang + side * spread + rnd.uniform(-12, 12)))
        grow(rnd, end, a2, length * rnd.uniform(0.6, 0.78), w1, depth - 1, paths, tips, spread, lo, hi, kids)


def blossom(pal):
    """A gnarled cherry tree in full bloom: clusters of blossom in many
    pinks, the dark limbs showing between them, petals drifting down
    and gathering on the ground; a snow-capped mountain behind in a
    pale pink dawn."""
    sky = pal.path("d2 d4 d6 a6 t7")
    mount = ridge([(0.4, 0.75, 0.38), (-1.6, 0.8, 0.2)], 0.72)
    rnd = random.Random(8)
    paths = [(bezier((1.47, 0.99), (1.38, 0.78), (1.46, 0.62), 10), 0.05, 0.04),
             (bezier((1.46, 0.62), (1.52, 0.55), (1.44, 0.48), 6), 0.04, 0.032)]
    tips = []
    for ang, ln, d in ((-160, 0.2, 4), (-128, 0.15, 4), (-95, 0.12, 3), (-60, 0.15, 4), (-22, 0.19, 4)):
        grow(rnd, (1.44, 0.5), ang, ln, 0.026, d, paths, tips)
    grow(rnd, (1.43, 0.7), -165, 0.2, 0.02, 3, paths, tips, lo=-178, hi=-120)   # a low limb, left
    grow(rnd, (1.47, 0.66), -15, 0.16, 0.018, 3, paths, tips, lo=-60, hi=10)    # and right
    tree = limbs(paths)

    # blossom: separate clusters at the forks and twig ends, some in front
    # of the limbs, some behind; each in its own pink
    shades = [pal.path("x8 x9 a5 a6 a8 t9"), pal.path("e9 a4 a6 a7 t9"), pal.path("a3 a5 a6 a8 t9"),
              pal.path("x7 e9 a6 a6 a9"), pal.path("a4 a6 a8 t9 t9")]
    clusters, grid = [], {}
    for x, y, depth in tips:
        if depth > 2 or y > 0.72 or rnd.random() < 0.25:
            continue
        for _ in range(1 if depth else 2):
            cx, cy = x + rnd.uniform(-0.03, 0.03), y + rnd.uniform(-0.03, 0.02)
            r = rnd.uniform(0.024, 0.044) * (1.15 if depth else 1)
            k = len(clusters)
            clusters.append((cx, cy, r, rnd.choice(shades), rnd.random() < 0.45, k, rnd.uniform(-0.25, 0.12)))
            for gx in range(math.floor((cx - r) / 0.05), math.floor((cx + r) / 0.05) + 1):
                for gy in range(math.floor((cy - r) / 0.05), math.floor((cy + r) / 0.05) + 1):
                    grid.setdefault((gx, gy), []).append(clusters[-1])

    def bloom(x, y, front):
        for cx, cy, r, shade, fr, k, tone in grid.get((math.floor(x / 0.05), math.floor(y / 0.05)), ()):
            if fr != front:
                continue
            dx, dy = (x - cx) / r, (y - cy) / r * 1.15
            d = math.hypot(dx, dy)
            if d < 1 - 0.45 * noise(x * 70, y * 70, k):
                floret = noise(x * 160, y * 130, k + 5)
                if floret < 0.3 and d > 0.3:
                    continue                                    # gaps between the flowers
                light = clamp(0.5 + tone - dx * 0.35 - dy * 0.45 - d * 0.2 + (floret - 0.5) * 1.0)
                return shade(light)
        return None

    # loose petals in the air and on the ground
    pr = random.Random(21)
    petals = {}
    for _ in range(420):
        x = pr.uniform(-3.2, 1.9)
        near = math.exp(-((x - 1.3) / 1.1) ** 2)
        y = pr.uniform(0.15, 0.99) if pr.random() < 0.3 + 0.7 * near else pr.uniform(0.88, 0.99)
        petals[(round(x / 0.012), round(y / 0.016))] = pr.choice(("a6", "a8", "t9", "a9", "a7"))
    bark = pal.path("- x0 d0 x1 d1 d3")

    def field(x, y):
        c = bloom(x, y, True)
        if c:
            return c, 1.0, True, "bloom"
        hit = tree(x, y)
        if hit:
            t, nx, ny, k = hit
            light = round_light(nx, ny, -0.5, -0.65)
            lent = noise(x * 28, y * 170, k) > 0.74                 # cherry bark: horizontal lenticels
            c = bark(clamp(light * 0.85 + (noise(x * 50, y * 40, k) - 0.5) * 0.35 + (0.25 if lent else 0)))
            if ny < -0.3 and noise(x * 40, y * 40, 4) > 0.55:      # pink light caught on top of a limb
                c = mix(c, pal.rgb("a4"), 0.6)
            return c, 1.0, True, "tree"
        c = bloom(x, y, False)
        if c:
            return c, 1.0, True, "bloom"
        pk = petals.get((round(x / 0.012), round(y / 0.016)))
        if pk and y < 0.9 and math.hypot((x / 0.012 + 0.5) % 1 - 0.5, (y / 0.016 + 0.5) % 1 - 0.5) < 0.3:
            return pal.rgb(pk), 1.0, False, "petal"
        if y > 0.9:
            g = pal.path("g4 g1 -")(clamp((y - 0.9) * 8))
            under = math.exp(-((x - 1.4) / 0.45) ** 2) * (0.55 + 0.45 * noise(x * 30, y * 60, 9))
            if pk or noise(x * 90, y * 140, 3) < under * 0.8:
                return pal.path("a4 a6 a8 t9")(noise(x * 60, y * 90, 2)), 1.0, False, "ground"
            return g, 1.0, False, "ground"
        top = mount(x)
        if y >= top:
            snow = y - top < 0.06 + 0.02 * math.sin(x * 40)
            return (pal.path("t8 t6")((y - top) * 10) if snow else pal.path("d4 d1")((y - top) * 3)), 1.0, False, "mountain"
        return sky(clamp(y * 1.3)), 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd2 = random.Random(13)
        out = []
        for _ in range(rows * 4):
            x = rnd2.uniform(-3.0, 1.9)
            y = rnd2.uniform(0.05, 0.95)
            if field(x, y)[3] in ("sky", "mountain"):
                out.append((int((x - x_left) / cw), int(y / unit), rnd2.choice(".,'`*"),
                            rnd2.choice([pal.rgb("a8"), pal.rgb("a6"), pal.rgb("t9")]), False))
        return out

    return scene("cherry blossom", field, texts, inks={"bloom": "atxe", "sky": "datw", "tree": "dxa"})


# ---------------------------------------------------------------- lavender

def lavender(pal):
    """Rows of lavender bushes running to the horizon under a golden
    evening; a lone tree on a grassy rise, its limbs showing between
    clumps of leaves lit gold from the sun's side."""
    hz = 0.55
    vx = 0.6                                                   # where the rows meet
    sky = pal.path("d4 a4 e6 w6 w8")
    rnd = random.Random(4)
    paths = [(bezier((1.46, 0.6), (1.43, 0.52), (1.47, 0.44), 8), 0.026, 0.02)]
    tips = []
    for ang, ln, d in ((-150, 0.15, 3), (-118, 0.13, 3), (-88, 0.12, 3), (-58, 0.13, 3), (-28, 0.15, 3)):
        grow(rnd, (1.47, 0.45), ang, ln, 0.015, d, paths, tips, spread=34, kids=(2, 2, 3))
    tree = limbs(paths)
    clumps, grid = [], {}
    for x, y, depth in tips:
        if depth > 2 or (depth == 2 and rnd.random() < 0.5):
            continue
        for _ in range(2 if depth == 0 else 1):
            cx, cy = x + rnd.uniform(-0.03, 0.03), y + rnd.uniform(-0.035, 0.015)
            r = rnd.uniform(0.032, 0.052)
            k = len(clumps)
            clumps.append((cx, cy, r, rnd.random() < 0.5, k, rnd.uniform(-0.15, 0.1)))
            for gx in range(math.floor((cx - r) / 0.05), math.floor((cx + r) / 0.05) + 1):
                for gy in range(math.floor((cy - r) / 0.05), math.floor((cy + r) / 0.05) + 1):
                    grid.setdefault((gx, gy), []).append(clumps[-1])
    leaf = pal.path("- g0 g1 g2 g4 g6 w6")

    def foliage(x, y, front):
        for cx, cy, r, fr, k, tone in grid.get((math.floor(x / 0.05), math.floor(y / 0.05)), ()):
            if fr != front:
                continue
            dx, dy = (x - cx) / r, (y - cy) / r * 1.2
            d = math.hypot(dx, dy)
            if d < 1 - 0.5 * noise(x * 60, y * 60, k):
                tuft = noise(x * 130, y * 110, k + 3)
                if tuft < 0.3 and d > 0.3:
                    continue                                    # sky through the leaves
                light = clamp(0.45 + tone - dx * 0.4 - dy * 0.25 - d * 0.15 + (tuft - 0.5) * 0.8)
                return leaf(light)
        return None

    bark = pal.path("- x0 d0 x1 w1")
    bush = pal.path("x1 d2 a3 a5 a7 a9")

    def field(x, y):
        c = foliage(x, y, True)
        if c:
            return c, 1.0, True, "tree"
        hit = tree(x, y)
        if hit:
            t, nx, ny, k = hit
            light = round_light(nx, ny, -0.85, -0.2)
            return bark(clamp(light * 0.85 + (noise(x * 60, y * 30, k) - 0.5) * 0.3)), 1.0, True, "tree"
        c = foliage(x, y, False)
        if c:
            return c, 1.0, True, "tree"
        rise = hz - 0.035 * math.exp(-((x - 1.46) / 0.28) ** 2)
        if rise <= y < hz + 0.05 * math.exp(-((x - 1.46) / 0.3) ** 2):
            blade = noise(x * 140, y * 30, 6)
            return pal.path("g0 g1 g2 g4 w4")(clamp(0.3 + blade * 0.5 - (y - rise) * 4)), 1.0, False, "grass"
        hill = hz - 0.02 - 0.025 * fbm(x * 2.5, 1.0, 2) - 0.012 * noise(x * 14, 2.0, 5)
        if hill <= y < hz:                                     # far hills in the haze
            return pal.path("e4 d4 d3")(clamp((y - hill) / 0.05)), 1.0, False, "sky"
        if y < hz:
            d = math.hypot(x - vx, y - hz)
            c = sky(clamp(y / hz + math.exp(-(d / 0.4) ** 2) * 0.3))
            k = soft_clouds([(0.3, 0.22, 0.5, 0.03), (1.3, 0.15, 0.4, 0.025), (-1.0, 0.25, 0.6, 0.03)])(x, y)
            return mix(c, pal.rgb("e6"), clamp(k * 1.2)), 1.0, False, "sky"
        # the rows: bushes in perspective, lit from behind, dark soil between
        t = (y - hz) / (1 - hz)
        z = 1 / (t + 0.02)
        rowpos = (x - vx) * z * 6
        row = math.floor(rowpos + 0.5)
        u = rowpos - row                                       # -0.5 .. 0.5 across a row
        fade = clamp((t - 0.12) / 0.35)
        lump = math.sin(z * 2.4 + row * 1.7) * 0.5 + 0.5      # bush after bush along the row
        hw = 0.33 + 0.12 * lump * fade + (1 - fade) * 0.25
        if abs(u) < hw:
            s = u / hw
            light = math.sqrt(1 - s * s) * 0.75 + lump * 0.15 * fade
            spike = noise(rowpos * 9, y * 260, 7) - 0.5         # flower spikes
            base = 0.62 - t * 0.2                               # paler into the haze
            light = base + (light - base) * fade + spike * 0.5 * fade ** 2
            return bush(clamp(light)), 1.0, False, "field"
        soil = noise(x * 50, y * 120, 8)
        return pal.path("x0 x1 g0 g1 g2")(clamp(soil * 0.6 + (0.5 - abs(u)) * 1.5)), 1.0, False, "field"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 2, 0.2, [pal.rgb("t8")], 5, chars="..·")

    return scene("lavender", field, texts, inks={"tree": "gdwx"})


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

    # a clownfish: orange, three white bands, a fin top and bottom, an eye -
    # big enough that the bands actually land on the grid
    clown = (0.95, 0.3, 0.08, 1)

    def clownfish(x, y):
        fx_, fy_, s, flip = clown
        u, v = (x - fx_) / s * flip, (y - fy_) / (s * 1.5)
        body = u * u + (v * 1.1) ** 2 <= 1
        tail = -1.8 < u < -0.9 and abs(v) < (u + 1.8) * 1.3
        fin = abs(u) < 0.6 and 0.8 < abs(v) < 1.5
        if not (body or tail or fin):
            return None, False
        band = abs(u + 0.52) < 0.16 or abs(u - 0.02) < 0.14 or abs(u - 0.62) < 0.13
        eye = ((u - 0.5) * 1.9) ** 2 + ((v + 0.42) * 1.9) ** 2 < 0.07
        edge = not (body and ((u - 0.02) ** 2 + (v * 1.05) ** 2 < 0.82)) or tail or fin
        return band, (eye or edge)

    # a jellyfish: a striped bell with long trailing tentacles
    jelly = (1.45, 0.2, 0.13)

    def jellyfish(x, y):
        jx, jy, jr = jelly
        u, v = (x - jx) / jr, (y - jy) / (jr * 1.7)
        if u * u + v * v <= 1:
            if v < -0.15 * (1 - u * u):
                return False, False                     # the gap under the bell
            rib = int((u + 1.4) * 3.1) % 2
            return bool(rib), (abs(v) > 0.78 or abs(u) > 0.86)
        if 1.0 < v < 2.6 and abs(u) < 0.5:
            wobble = 0.12 * math.sin(v * 5 + jx)
            if abs(abs(u) - 0.28) < 0.06 or abs(u - wobble) < 0.05:
                return True, True
        return None, False

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
        band, dark = clownfish(x, y)
        if band or dark:
            if dark:
                return pal.rgb("d1"), 1.0, True, "fish"
            return (pal.rgb("w9") if band else pal.rgb("e6")), 1.0, True, "fish"
        jband, jedge = jellyfish(x, y)
        if jband or jedge:
            if jedge:
                return pal.rgb("a8"), 1.0, True, "jelly"
            # the bell is a jelly: only its ribs and rim take colour, the
            # rest is water seen through it
            return pal.path("a4 a6 w6")(clamp(0.35 + (jelly[1] - y) * 3)), 0.34, True, "jelly"
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

    return scene("coral reef", field, texts,
                 inks={"water": "gdt", "coral": "eawx", "fish": "eaxwd", "jelly": "awxe"})


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
        # no window (the owner wanted just the mug): the light it threw is
        # still on the wall, warm and soft against the darkening room
        glow = math.exp(-((x - 0.05) / 0.95) ** 2 - ((y - 0.42) / 0.55) ** 2)
        c = pal.path("- d1 x1 a4")(clamp(glow * 0.85))
        return c, 1.0, False, "wall"

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
