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
        return sky(clamp(y / 0.66) ** 1.3), False, "sky"   # clamped first: y < 0 above the picture

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
            return mix(c, pal.rgb("e8"), horizon_glow(x, y)), 1.0, foc, tag
        depth = (y - hz) / (1 - hz)
        wob = 0.006 * math.sin(y * 260 + 2 * math.sin(x * 14))
        c, _, tag = air(x + wob, clamp(hz - (y - hz) * 1.3, 0.0, hz - 0.001))
        c = mix(c, pal.rgb("a1"), 0.2 + depth * 0.55)
        c = mix(c, pal.rgb("e8"), horizon_glow(x, y))
        width = 0.06 + depth * 0.22
        glint = noise(x * 28, y * 160, 7) > 0.55 - 0.15 * (1 - depth)
        off = abs(x - sx + wob * 2) / width
        if off < 1 and glint:
            c = mix(c, pal.rgb("t9" if off < 0.4 and depth < 0.5 else "e9"), (1 - off ** 2) * (1 - depth * 0.45))
        elif glint and noise(x * 9, y * 40, 2) > 0.62:
            c = mix(c, pal.rgb("e6"), 0.35 * near_sun(x))
        return c, 1.0, False, "lake"

    def horizon_glow(x, y):
        """Light pooled along the water line, brightest under the sun."""
        return 0.75 * math.exp(-((y - hz) / 0.018) ** 2) * math.exp(-((x - sx) / 0.35) ** 2)

    def near_sun(x):
        return math.exp(-((x - sx) / 0.7) ** 2) + 0.2

    def texts(rows, x_left, cw, unit):
        out = []
        for x, y in ((0.72, 0.17), (0.79, 0.14), (0.85, 0.19), (0.3, 0.11), (1.65, 0.09)):
            out.append((int((x - x_left) / cw), int(y / unit), "v", pal.rgb("x1"), False))
        return out

    return scene("solarized", field, texts, inks={"sky": "axew", "cloud": "axew", "sun": "tew", "ridge": "axew", "lake": "axetw"})


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
                if any(brace(x + (k + 0.5 + dx) * cw, y + dy * unit) for k in range(len(tok))
                       for dx in (-1.5, -0.5, 0.5, 1.5) for dy in (-0.4, 0.4)):
                    continue                                  # a clear cell around the braces
                for k, ch in enumerate(tok):
                    xx = x + (k + 0.5) * cw
                    if ch == " " or (r, c + k) in taken or c + k >= cols:
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
    leafy = pal.path("d1 g1 g2 g4 a6")         # no green in rose pine: its deepest teal greys up to foam
    spine = bezier(base, (cx + 0.07, 0.68), (cx - 0.02, 1.04), 24)
    stem = strokes([(spine, 0.013, 0.011)])
    calyx = (cx, cy + 0.15)
    sepals = strokes([(bezier(calyx, (cx + dx * 1.1, calyx[1] + dy * 0.45), (cx + dx * 0.8, calyx[1] + dy), 12),
                       0.03, 0.012) for dx, dy in ((-0.17, 0.16), (0.0, 0.17), (0.18, 0.15))])
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
            return leafy(clamp(0.8 - (x - cx + 0.03) * 10)), 1.0, True, "stem"
        s = sepals(x, y)
        if s is not None:
            return leafy(0.75 - 0.4 * s), 1.0, True, "stem"
        if stem(x, y) is not None or thorn(x, y):
            lit = stem(x - 0.008, y) is None and not thorn(x - 0.008, y)
            return leafy(0.7 if lit else 0.25), 1.0, True, "stem"
        lf = leaf(x, y)
        if lf:
            s, w = lf
            vein = abs(w) < 0.1 or (s * 9 - abs(w) * 1.4) % 1 < 0.14
            c = leafy(clamp(0.3 + 0.4 * (w < 0) + 0.25 * (1 - s) - 0.15 * abs(w) ** 3))
            return (leafy(0.05) if vein else c), 1.0, True, "leaf"
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

    return scene("rose pine", field, texts, inks={"rose": "ex", "dark": "dxw", "leaf": "dga", "stem": "dga"})



MORE = {"jungle": jungle, "blossom": blossom, "lavender": lavender, "snowpeaks": snowpeaks,
        "reef": reef, "volcano": volcano, "bamboo": bamboo, "bat": bat, "mountains": mountains,
        "coffee": coffee, "sun": sun, "code": code, "cat": cat, "rose": rose}
