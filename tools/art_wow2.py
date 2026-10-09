"""More "wow" pictures for the revamp style (see art_wow.py): the rest of
the themes, each a colour field in its own theme's palette, built with
the combined renderer. Registered into art_wow.WOW at the bottom of
art_wow.py.

Palette letters: d dim, t text, e error, x extra, a accent, g good,
w warn; tone 0 (dark) .. 9 (light); "-" the ground.
"""

import math
import random

from art_combined import Scene, mix
from art_wow import SHADE, SIZES, palm, pine, ridge, sphere_light, stars


# ---------------------------------------------------------------- helpers

def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) / 0xFFFFFFFF


def noise(x, y, seed=0):
    """Smooth value noise, 0..1."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def fbm(x, y, seed=0, octaves=3):
    """Noise in a few octaves, 0..1."""
    total, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        total += noise(x * 2 ** o, y * 2 ** o, seed + o * 17) * amp
        norm += amp
        amp *= 0.5
    return total / norm


def blob(cx, cy, rx, ry):
    """Inside an ellipse (cells are tall: ry is in picture units too)."""
    def inside(x, y):
        return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
    return inside


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def soft_clouds(spec):
    """Long soft clouds: spec [(cx, cy, w, h)]; returns 0..1 density."""
    def at(x, y):
        best = 0.0
        for cx, cy, w, h in spec:
            d = ((x - cx) / w) ** 2 + ((y - cy) / h) ** 2
            if d < 1:
                best = max(best, (1 - d) * (0.75 + 0.25 * noise(x * 12, y * 30, 3)))
        return best
    return at


def scene(theme, field, texts=None, lines=None, inks=None):
    return Scene(1.9, field, lines, texts, span=True, sizes=SIZES, shade_cost=SHADE,
                 theme=theme, inks=inks)


# ---------------------------------------------------------------- sunset

def sunset(pal):
    """A huge sun sinking into the sea, the sky burning from violet to
    gold, long clouds lit from below, a glittering path on the water and
    a sailboat crossing it."""
    hz = 0.62
    sx, sy, sr = 1.2, 0.56, 0.19
    sky = pal.path("x1 x4 e4 e6 a6 a8")
    sea = pal.path("e4 x4 x1 -")
    disc = pal.path("w9 w8 a8 a6")
    clouds = soft_clouds([(1.0, 0.36, 0.55, 0.03), (1.5, 0.45, 0.4, 0.022), (0.3, 0.28, 0.6, 0.03),
                          (-0.7, 0.4, 0.7, 0.025), (-1.9, 0.3, 0.6, 0.03), (0.6, 0.5, 0.35, 0.018)])

    def boat(x, y):
        bx, by = 1.62, 0.8
        if by - 0.012 <= y <= by + 0.03 and abs(x - bx) <= 0.13 - (y - by + 0.012) * 1.2:
            return True                                       # the hull
        if by - 0.27 <= y <= by - 0.015:                       # sails
            t = (by - 0.015 - y) / 0.255
            if bx - 0.005 <= x <= bx + 0.11 * (1 - t) and t < 0.97:
                return True
            if bx - 0.09 * (1 - t) ** 1.2 <= x <= bx - 0.012 and t < 0.8:
                return True
            if abs(x - bx) < 0.006:
                return True
        return False

    def field(x, y):
        if boat(x, y):
            rim = not boat(x - 0.01, y) and y < 0.8
            return (pal.rgb("a6") if rim else pal.ground), 1.0, True, "boat"
        d = math.hypot(x - sx, y - sy)
        if y < hz:
            if d <= sr:
                t = (y - sy + sr) / (2 * sr)
                band = y > sy + 0.02 and math.sin((y - sy) * 140) > 0.65 - (y - sy) * 6
                return (pal.rgb("e6") if band else disc(t)), 1.0, True, "sun"
            c = sky(clamp(y / hz + math.exp(-(d / 0.5) ** 2) * 0.3))
            k = clouds(x, y)
            if k:
                under = clamp((y - 0.25) * 4)
                lit = mix(pal.rgb("x4"), pal.rgb("w8"), under * math.exp(-((x - sx) / 0.9) ** 2))
                c = mix(c, lit, clamp(k * 1.6))
            return c, 1.0, False, "sky"
        t = (y - hz) / (1 - hz)
        c = sea(t)
        width = 0.18 * (1 - t * 0.4) + t * 0.15
        glint = math.sin(x * 60 + y * 400 + 4 * math.sin(x * 7)) > 0.3 and math.sin(y * 210) > -0.3
        if abs(x - sx) < width and glint:
            c = mix(c, pal.rgb("w8"), (0.9 - t * 0.5) * (1 - abs(x - sx) / width))
        elif glint and t > 0.15:
            c = mix(c, pal.rgb("e4"), 0.3)
        if y < hz + 0.04 and d <= sr * 1.1:                      # the sun's lower half, mirrored
            c = mix(c, pal.rgb("a8"), 0.6)
        return c, 1.0, False, "sea"

    def texts(rows, x_left, cw, unit):
        out = stars(field, rows, x_left, cw, unit, rows * 3, 0.2, [pal.rgb("t8"), pal.rgb("w9")], 4,
                    chars="..·'")
        for x, y in ((0.75, 0.25), (0.82, 0.22), (0.9, 0.27), (-0.5, 0.2), (-0.42, 0.23)):
            out.append((int((x - x_left) / cw), int(y / unit), "v", pal.rgb("x1"), x > 0.7))
        return out

    return scene("sunset", field, texts, lambda rows: [
        ([(-6.0, hz), (2.0, hz)], pal.rgb("a8"), False, None)])


# ---------------------------------------------------------------- moss

def _fern(cx, base, size, seed):
    """A fern clump rooted at (cx, base): a few big fronds that rise and
    arch outward, each a midrib with leaflets, and a few grass blades.
    inside(x, y) -> 0..1 along the frond (root to tip), or None."""
    rnd = random.Random(seed)
    fronds = []
    for lean in (-1.0, 0.15 * rnd.choice((-1, 1)), 1.0):
        ln = size * rnd.uniform(0.85, 1.1)
        tip = (cx + lean * ln * 0.9, base - ln * (0.75 - 0.4 * abs(lean)))
        ctrl = (cx + lean * ln * 0.35, base - ln * (1.15 - 0.2 * abs(lean)))
        n = 14
        pts = [((1 - t) ** 2 * cx + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0],
                (1 - t) ** 2 * base + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1])
               for t in (k / n for k in range(n + 1))]
        fronds.append(pts)
    blades = [(cx + rnd.uniform(-0.4, 0.4) * size, size * rnd.uniform(0.5, 0.9), rnd.uniform(-0.6, 0.6))
              for _ in range(3)]

    def inside(x, y):
        if abs(x - cx) > size * 1.05 or y > base + 0.004 or y < base - size * 1.1:
            return None
        for bx, bh, lean in blades:                 # grass blades among the fronds
            dy = base - y
            t = dy / bh
            if 0 <= t <= 1 and abs(x - bx - lean * dy * t) < 0.005 * (1 - t) + 0.0015:
                return t * 0.8
        for pts in fronds:
            n = len(pts) - 1
            for k in range(n):
                (ax, ay), (bx, by) = pts[k], pts[k + 1]
                dx, dy = bx - ax, by - ay
                u = clamp(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy))
                d = math.hypot(x - ax - dx * u, y - ay - dy * u)
                t = (k + u) / n
                if d > 0.03:
                    continue
                if d < 0.0035:
                    return t                            # the midrib
                # leaflets: broad in the middle, tapering to the tip, with gaps
                leaf = 0.024 * math.sin(math.pi * min(1.0, 0.2 + t)) * (1 - t * 0.5) * (0.6 + 0.4 * ((t * 8) % 1.0))
                if d < leaf:
                    return t + (0.3 if y < ay + dy * u else 0.0)   # upper side catches light
        return None
    return inside


def _vine(tx, w, seed):
    """A vine climbing a trunk at tx (half width w): inside(x, y) gives
    'stem', 'leaf' or None."""
    ph = seed * 1.7

    def inside(x, y):
        s = math.sin(y * 38 + ph)
        if math.cos(y * 38 + ph) < -0.2:          # round the back of the trunk
            return None
        vx = tx + w * 0.9 * s
        if abs(x - vx) < 0.0045:
            return "stem"
        # leaves in pairs every so often along the stem
        k = math.floor(y * 55 + ph)
        if noise(k * 1.3, seed, 5) > 0.35:
            ly = (k + 0.5) / 55 - ph / 55
            side = 1 if k % 2 else -1
            lx = vx + side * 0.012
            if ((x - lx) / 0.011) ** 2 + ((y - ly) / 0.009) ** 2 <= 1:
                return "leaf"
        return None
    return inside


def stones(pal):
    """A cairn of weathered, moss-capped stones in a misty clearing, light
    falling through the trees; vines climb every other trunk and ferns
    and grass spring up at their feet."""
    ground_y = 0.88
    stack = [(1.3, 0.83, 0.22, 0.075), (1.27, 0.7, 0.17, 0.06), (1.33, 0.59, 0.13, 0.05),
             (1.29, 0.495, 0.095, 0.042), (1.31, 0.42, 0.065, 0.032), (1.3, 0.365, 0.04, 0.024)]
    rocks = [(1.72, 0.86, 0.12, 0.05), (0.9, 0.87, 0.1, 0.04)]
    rnd = random.Random(11)
    trunks = sorted((rnd.uniform(-3.4, 1.9), rnd.uniform(0.02, 0.05), rnd.uniform(0.0, 1.0)) for _ in range(26))
    vines = {k: _vine(tx, w, k) for k, (tx, w, _) in enumerate(trunks) if k % 2 == 0}
    ferns = []
    for k, (tx, w, _) in enumerate(trunks):        # a big fern at every trunk's foot
        side = 1 if k % 3 else -1
        fx = tx + side * (w + rnd.uniform(0.01, 0.04))
        ferns.append((fx, _fern(fx, ground_y + 0.012, rnd.uniform(0.16, 0.22), k)))
    for fx in (1.02, 1.6):                          # and round the cairn
        ferns.append((fx, _fern(fx, ground_y + 0.012, 0.13, int(fx * 100))))
    stone = pal.path("- t0 t1 t3 t5 t6")
    moss = pal.path("a0 a1 g2 g4 g6 g7")
    bark = pal.path("- a0 d0 d2 d4 t1")
    every = stack + rocks

    def in_stone(x, y):
        for k, (cx, cy, rx, ry) in enumerate(every):
            ang = math.atan2((y - cy) / ry, (x - cx) / rx)
            wob = 1 + 0.09 * (noise(ang * 1.6 + 4, k, 21) - 0.5) + 0.04 * (noise(ang * 5, k, 22) - 0.5)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= wob * wob:
                return k, cx, cy, rx * wob, ry * wob
        return None

    rifts = {0: [(-0.35, -0.75), (-0.25, -0.2), (-0.38, 0.25), (-0.3, 0.85)],
             2: [(0.3, -0.8), (0.22, -0.1), (0.36, 0.4), (0.28, 0.9)],
             len(stack): [(-0.1, -0.7), (0.05, 0.0), (-0.05, 0.8)]}

    def cracks(k, u, v):
        """A jagged crack down a few of the stones (u, v the stone's own
        -1..1 coordinates): 'crack', 'lip' or None."""
        pts = rifts.get(k)
        if not pts:
            return None
        for (au, av), (bu, bv) in zip(pts, pts[1:]):
            if av <= v <= bv:
                cu = au + (bu - au) * (v - av) / (bv - av)
                if abs(u - cu) < 0.06:
                    return "crack"
                if 0.06 <= cu - u < 0.13:
                    return "lip"
        return None

    def beam_at(x, y):
        return clamp(math.sin((x * 0.6 + y * 0.35) * 9) * 0.5 + 0.5) ** 6 * (1 - y)

    def brush(x, y):
        """Ferns and grass at the trunks' feet: colour, or None."""
        for fx, fern in ferns:
            if abs(x - fx) < 0.24:
                t = fern(x, y)
                if t is not None:
                    return pal.path("- a0 a1 g2 g4 g6")(clamp(0.2 + t * 0.55 + beam_at(x, y) * 0.3))
        return None

    def field(x, y):
        s = in_stone(x, y)
        if s:
            k, cx, cy, rx, ry = s
            light = sphere_light(cx, cy, max(rx, ry * 2), -0.5, -0.7)(x, cy + (y - cy) * 2)
            grain = (fbm(x * 40, y * 80, k) - 0.5) * 0.3
            c = stone(clamp(light ** 1.4 * 1.05 + grain))
            if k < len(stack) - 1 and (cy + ry - y) < ry * 0.25:   # shadow where it sits
                c = mix(c, pal.ground, 0.35)
            top = (cy - y) / ry                      # 1 at the top, -1 at the bottom
            fuzz = fbm(x * 70, y * 120, k + 30)
            cap = top > 0.4 + (0.5 - fuzz) * 1.1 + (x - cx) / rx * 0.2
            drip = fuzz > 0.66 and top > -0.5 and abs(x - cx) < rx * 0.7
            if cap or drip:                          # moss cushions on top, creeping down
                c = moss(clamp(light * 0.75 + (fuzz - 0.5) * 0.9))
            else:
                if noise(x * 160, y * 260, k + 50) > 0.84:
                    c = mix(c, pal.rgb("w6"), 0.55)   # lichen
            crack = cracks(k, (x - cx) / rx, (y - cy) / ry)
            if crack == "crack":
                c = mix(c, pal.ground, 0.85)
            elif crack == "lip":
                c = mix(c, pal.rgb("t7"), 0.45)        # the crack's lit lip
            return c, 1.0, True, "stone"
        b = brush(x, y)
        if b is not None:
            return b, 1.0, False, "ferns"
        if y >= ground_y:
            blade = math.sin(x * 160 + math.sin(x * 23) * 3) * 0.5 + 0.5
            if y - ground_y < 0.05 * blade + 0.01:
                return pal.path("- a0 g1 a4")(blade * 0.8 + 0.1), 1.0, False, "ferns"
            return pal.path("g1 d1 -")((y - ground_y) * 6), 1.0, False, "ground"
        beam = beam_at(x, y)
        for k, (tx, w, depth) in enumerate(trunks):
            lean = (y - 0.5) * 0.02
            flare = w * (1 + 1.6 * math.exp(-(ground_y - y) / 0.025))   # roots spread at the foot
            u = (x - tx - lean) / flare
            if abs(u) < 1:
                v = vines.get(k)
                part = v(x - lean, y) if v else None
                if part == "stem":
                    return pal.path("a0 g1 g3")(clamp(0.6 - u * 0.4)), 1.0, False, "vine"
                if part == "leaf":
                    return pal.path("a1 g2 g4 g6")(clamp(0.55 - u * 0.4 + beam * 0.4)), 1.0, False, "vine"
                groove = noise(u * 5 + k * 7, y * 5, 60)    # bark furrows
                lum = 0.45 - u * 0.3 + (groove - 0.5) * 0.5 + depth * 0.15
                if abs(u) > 0.8 and u < 0:
                    lum += 0.2                          # rim light on the lit side
                c = bark(clamp(lum))
                return mix(c, pal.rgb("a4"), beam * 0.3), 1.0, False, "trees"
            if v := vines.get(k):
                if abs(x - tx - lean) < flare + 0.02 and v(x - lean, y) == "leaf":
                    return pal.path("a1 g2 g4 g6")(clamp(0.5 + beam * 0.4)), 1.0, False, "vine"
        canopy = fbm(x * 3, y * 6, 2)
        c = pal.path("- g1 d1 a1 a4")(clamp(y * 0.9 + canopy * 0.35 - 0.1))
        mist = math.exp(-((y - 0.78) / 0.12) ** 2) * 0.55
        c = mix(c, pal.rgb("t4"), mist * (0.6 + 0.4 * noise(x * 4, 1)))
        c = mix(c, pal.rgb("w6"), beam * 0.45)
        return c, 1.0, False, "wood"

    def texts(rows, x_left, cw, unit):
        rnd2 = random.Random(5)
        out = []
        for _ in range(rows * 2):                  # motes in the light
            x, y = rnd2.uniform(-3.0, 1.9), rnd2.uniform(0.1, 0.8)
            if field(x, y)[3] == "wood":
                out.append((int((x - x_left) / cw), int(y / unit), rnd2.choice(".·'"),
                            pal.rgb("w8"), False))
        return out

    return scene("moss", field, texts, inks={"stone": "dxtgaw", "wood": "dgat w", "trees": "dta",
                                             "vine": "ga", "ferns": "ga"})


# ---------------------------------------------------------------- pine

def lone_pine(pal):
    """A lone pine on a rocky point over a still lake at dawn, mountains
    and their reflection, mist on the water."""
    shore = 0.66
    far = ridge([(0.3, 0.55, 0.26), (1.0, 0.5, 0.32), (1.75, 0.45, 0.22), (-0.8, 0.7, 0.28), (-2.0, 0.7, 0.22)], shore)
    sky = pal.path("d1 a1 a4 g4 w6")
    tree = pine(1.42, 0.82, 0.66, 0.24, 8)
    tree2 = pine(1.73, 0.84, 0.38, 0.14, 6)

    def rock(x, y):
        top = 0.8 + 0.08 * ((x - 1.5) / 0.45) ** 2 + 0.01 * math.sin(x * 70)
        return abs(x - 1.5) < 0.45 and y >= top

    def field(x, y):
        if tree(x, y) or tree2(x, y):
            rim = not (tree(x + 0.012, y) or tree2(x + 0.012, y))
            return (pal.rgb("g4") if rim else pal.ground), 1.0, True, "tree"
        if rock(x, y):
            return pal.path("x4 d1 -")(clamp((y - 0.8) * 5 + fbm(x * 30, y * 30) * 0.3)), 1.0, True, "rock"
        if y < shore:
            top = far(x)
            if y >= top:
                c = pal.path("a4 a1 d1")((y - top) * 4)
                snow = y - top < 0.025 and top < shore - 0.18
                return (pal.rgb("t6") if snow else c), 1.0, False, "mountains"
            c = sky(clamp(y / shore * 1.1))
            return mix(c, pal.rgb("w8"), math.exp(-(((x - 0.9) / 0.6) ** 2 + ((y - shore) / 0.12) ** 2)) * 0.5), \
                1.0, False, "sky"
        # the lake: the scene above, mirrored and darker, with ripples
        my = shore - (y - shore) * 1.3 + 0.004 * math.sin(y * 300 + x * 8)
        c, _, _, tag = field(x, clamp(my, 0.0, shore - 0.001))
        c = mix(c, pal.ground, 0.35 + (y - shore) * 0.8)
        mist = math.exp(-((y - shore - 0.02) / 0.05) ** 2) * 0.5
        return mix(c, pal.rgb("t4"), mist), 1.0, False, "lake"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 3, 0.25, [pal.rgb("t8"), pal.rgb("t6")], 2,
                     chars="..·")

    return scene("pine", field, texts)


# ---------------------------------------------------------------- autumn

def leaf(pal):
    """A big maple leaf drifting down in front of an autumn wood - red
    and gold, veined, lit from the left - with more leaves falling."""
    cx, cy, size = 1.28, 0.47, 0.4
    ang0 = math.radians(-18)

    def maple(x, y):
        """0..1 inside the leaf (by how far in), or -1 outside; and the
        polar angle."""
        u, v = (x - cx) / size, (y - cy) / size
        u, v = u * math.cos(ang0) - v * math.sin(ang0), u * math.sin(ang0) + v * math.cos(ang0)
        r, a = math.hypot(u, v * 1.0), math.atan2(-v, u)
        lobes = 0.55 + 0.32 * abs(math.cos(a * 2.5)) ** 0.6 + 0.12 * abs(math.sin(a * 9)) ** 3
        if a < -1.2 and a > -1.95:                     # the bottom notch where the stem goes
            lobes *= 0.55 + 0.45 * abs(a + 1.57) / 0.38
        return (1 - r / lobes) if r <= lobes else -1, a, u, v

    def stem(x, y):
        u, v = (x - cx) / size, (y - cy) / size
        u, v = u * math.cos(ang0) - v * math.sin(ang0), u * math.sin(ang0) + v * math.cos(ang0)
        return 0.0 < v < 0.75 and abs(u - v * v * 0.15) < 0.025

    flesh = pal.path("e1 e4 e6 a6 w6 w8")

    def field(x, y):
        inside, a, u, v = maple(x, y)
        if inside >= 0 or stem(x, y):
            if inside < 0:
                return pal.rgb("x4"), 1.0, True, "leaf"
            vein = any(abs(math.sin(a - va)) * math.hypot(u, v) < 0.022 and math.cos(a - va) > 0
                       for va in (math.pi / 2, math.pi / 2 + 1.1, math.pi / 2 - 1.1, math.pi / 2 + 2.1,
                                  math.pi / 2 - 2.1))
            light = clamp(0.35 + 0.5 * (-u * 0.6 - v * 0.4) + inside * 0.4 + fbm(x * 20, y * 20, 4) * 0.25)
            c = flesh(light)
            if vein:
                c = mix(c, pal.rgb("w8"), 0.6)
            if inside < 0.06:
                c = mix(c, pal.rgb("e1"), 0.5)            # a darker rim
            return c, 1.0, True, "leaf"
        # the wood behind: trunks, a glowing canopy, a path of leaves
        canopy = fbm(x * 2.5, y * 4, 9, 4)
        if y > 0.86:
            litter = fbm(x * 18, y * 30, 5)
            return pal.path("- x1 e1 e4 a4")(clamp(litter * 0.9 - (y - 0.86) * 3)), 1.0, False, "ground"
        for tx in (-2.9, -2.3, -1.7, -1.05, -0.5, 0.1, 0.7, 1.75):
            w = 0.03 + 0.02 * math.sin(tx * 5) ** 2
            if abs(x - tx - (0.86 - y) * 0.04 * math.sin(tx * 3)) < w and y > 0.3 + 0.1 * math.sin(tx * 7):
                return mix(pal.ground, pal.rgb("x1"), 0.6), 1.0, False, "trees"
        glow = math.exp(-(((x - 0.3) / 1.2) ** 2 + ((y - 0.6) / 0.45) ** 2))
        c = pal.path("- x1 e1 e4 a4")(clamp(canopy * 0.55 + glow * 0.4 - y * 0.25))
        return c, 1.0, False, "wood"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(7)
        out = []
        for _ in range(rows):
            x, y = rnd.uniform(-3.0, 1.9), rnd.uniform(0.05, 0.85)
            if field(x, y)[3] in ("wood", "trees"):
                out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("*%&,'"),
                            rnd.choice([pal.rgb("e6"), pal.rgb("a6"), pal.rgb("w6"), pal.rgb("a8")]), False))
        return out

    return scene("autumn", field, texts, inks={"leaf": "eawx", "wood": "xeaw", "ground": "xeaw"})


# ---------------------------------------------------------------- desert

def cactus(pal):
    """A tall saguaro at golden hour: ribbed and lit from the setting
    sun, mesas on the horizon, dunes rippling away."""
    hz = 0.7
    sx, sy, sr = 0.55, 0.62, 0.09
    sky = pal.path("x1 e4 a4 a6")
    mesas = [(-0.1, 0.42, 0.13), (0.95, 0.3, 0.08), (-1.3, 0.5, 0.16), (-2.4, 0.35, 0.1)]
    arms = [  # (x of the arm's foot on the trunk, height it leaves, side, reach, rise)
        (1.36, 0.58, -1, 0.15, 0.24), (1.36, 0.44, 1, 0.13, 0.28)]
    tx, tw, top = 1.36, 0.068, 0.08

    def saguaro(x, y):
        """(distance across, 0..1 from its left edge) if inside, else None."""
        if y >= top and abs(x - tx) <= tw * (1 if y > top + tw else math.sqrt(max(0.0, 1 - ((top + tw - y) / tw) ** 2))):
            return (x - tx + tw) / (2 * tw)
        for fx, fy, side, reach, rise in arms:
            ax = fx + side * reach
            w = tw * 0.75
            # elbow: out sideways, then up
            if fy - w <= y <= fy + w and min(fx, ax) <= x <= max(fx, ax):
                return 0.5 + 0.3 * side
            ytop = fy - rise
            if ytop <= y <= fy and abs(x - ax) <= w * (1 if y > ytop + w else
                                                      math.sqrt(max(0.0, 1 - ((ytop + w - y) / w) ** 2))):
                return (x - ax + w) / (2 * w)
        return None

    def field(x, y):
        s = saguaro(x, y)
        if s is not None and y < 0.95:
            rib = 0.5 + 0.5 * math.cos(s * math.pi * 7)
            light = clamp(1.0 - s * 1.1) * 0.75 + rib * 0.25
            return pal.path("- g1 g4 g6 w6")(light), 1.0, True, "cactus"
        if y < hz:
            for mx, w, h in mesas:
                up = (y - (hz - h)) / h                 # 0 at the top, 1 at the foot
                if 0 <= up and abs(x - mx) < w * (1 + 0.35 * up ** 1.5):
                    face = (x - mx) / w
                    band = 0.12 * (math.sin(up * 22) > 0.6)
                    return pal.path("x1 x4 e4 a4")(clamp(0.75 - face * 0.35 - up * 0.3 + band)), 1.0, False, "mesa"
            d = math.hypot(x - sx, y - sy)
            if d < sr:
                return pal.path("w9 w8 a8")((y - sy + sr) / (2 * sr)), 1.0, False, "sun"
            c = sky(clamp(y / hz + math.exp(-(d / 0.4) ** 2) * 0.35))
            return c, 1.0, False, "sky"
        t = (y - hz) / (1 - hz)
        ripple = math.sin(x * 40 + math.sin(x * 3 + y * 20) * 2 + y * 90)
        c = pal.path("a6 a4 x4 x1 -")(clamp(t * 0.9 + ripple * 0.06))
        if ripple > 0.75 and t > 0.1:
            c = mix(c, pal.rgb("w8"), 0.35)
        shadow = 0.95 > y > 0.9 and tx - 0.6 < x < tx and abs(y - 0.92 + (tx - x) * 0.04) < 0.02
        if shadow:
            c = mix(c, pal.ground, 0.6)
        return c, 1.0, False, "sand"

    def texts(rows, x_left, cw, unit):
        out = stars(field, rows, x_left, cw, unit, rows * 2, 0.25, [pal.rgb("t8")], 6, chars="..·")
        rnd = random.Random(3)
        for _ in range(rows):                      # spines on the lit side
            y = rnd.uniform(top + 0.05, 0.9)
            x = tx - tw * rnd.uniform(0.9, 1.05)
            out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("'`,"), pal.rgb("w8"), True))
        return out

    return scene("desert", field, texts, inks={"cactus": "gw", "sand": "awx", "sky": "xeaw", "mesa": "xe"})


# ---------------------------------------------------------------- meadow

def flowers(pal):
    """Poppies and daisies up close, in a meadow rolling away under a big
    soft sky, petals catching the light."""
    rnd = random.Random(14)
    blooms = [(1.3, 0.4, 0.17, "e"), (1.64, 0.58, 0.12, "w"), (1.06, 0.64, 0.11, "e"),
              (1.8, 0.3, 0.1, "e"), (0.9, 0.44, 0.08, "w")]
    small = [(rnd.uniform(-3.2, 1.9), rnd.uniform(0.72, 0.95), rnd.uniform(0.012, 0.025),
              rnd.choice("eewa")) for _ in range(140)]
    hills = [ridge([(0.4, 0.9, 0.06), (1.4, 0.8, 0.08), (-1.0, 1.0, 0.07)], 0.62),
             ridge([(0.0, 0.8, 0.05), (1.1, 0.9, 0.06), (-1.8, 1.0, 0.06)], 0.7)]
    sky = pal.path("a1 g1 d4 t4 t6")
    clouds = soft_clouds([(0.8, 0.2, 0.4, 0.06), (1.6, 0.14, 0.3, 0.05), (-0.4, 0.25, 0.5, 0.06),
                          (-1.8, 0.18, 0.5, 0.05)])

    def bloom_at(x, y):
        for k, (bx, by, r, col) in enumerate(blooms):
            u, v = (x - bx) / r, (y - by) / (r * 0.85)
            d, a = math.hypot(u, v), math.atan2(v, u)
            petals = 0.72 + 0.28 * abs(math.cos(a * (2.5 if col == "e" else 6)))
            if d <= petals:
                return k, d, a, u, v, col
        return None

    def stem_at(x, y):
        for bx, by, r, col in blooms:
            if y > by and abs(x - bx - (y - by) * 0.08 * math.sin(bx * 9)) < 0.012:
                return True
        return False

    def field(x, y):
        b = bloom_at(x, y)
        if b:
            k, d, a, u, v, col = b
            if d < 0.28:
                return (pal.path("x1 d1")(d * 3) if col == "e" else pal.path("w6 a6 w8")(d * 3)), 1.0, True, "flower"
            light = clamp(0.55 - u * 0.25 - v * 0.3 + (1 - d) * 0.3)
            ramp = pal.path("e1 e4 e6 e8") if col == "e" else pal.path("t4 t6 t8 t9")
            c = ramp(light)
            if math.sin(a * (5 if col == "e" else 12)) > 0.85:
                c = mix(c, pal.ground, 0.25)              # the folds between petals
            return c, 1.0, True, "flower"
        if stem_at(x, y):
            return pal.rgb("g4"), 1.0, True, "stem"
        for sxx, syy, r, col in small:
            if math.hypot(x - sxx, (y - syy) * 1.2) < r:
                return pal.rgb(col + "6"), 1.0, False, "meadow"
        if y > hills[1](x):
            blade = math.sin(x * 220 + math.sin(x * 31) * 4) * 0.5 + 0.5
            c = pal.path("g6 g4 a4 g1 -")(clamp((y - 0.7) * 2.6 + blade * 0.15))
            return c, 1.0, False, "meadow"
        if y > hills[0](x):
            return pal.path("a4 g4 g1")(clamp((y - hills[0](x)) * 5)), 1.0, False, "hills"
        c = sky(clamp(y / 0.62))
        k = clouds(x, y)
        if k:
            c = mix(c, pal.rgb("t6"), clamp(k * 0.9))
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd2 = random.Random(9)
        out = []
        for _ in range(rows // 2):                  # butterflies and seeds
            x, y = rnd2.uniform(-2.5, 1.0), rnd2.uniform(0.3, 0.6)
            if field(x, y)[3] in ("sky", "hills"):
                out.append((int((x - x_left) / cw), int(y / unit), rnd2.choice("~*'"),
                            rnd2.choice([pal.rgb("w8"), pal.rgb("e8"), pal.rgb("t9")]), False))
        return out

    return scene("meadow", field, texts, inks={"sky": "agdt", "meadow": "gaewt", "hills": "ga"})


MORE = {"sunset": sunset, "stones": stones, "pine": lone_pine, "leaf": leaf, "cactus": cactus,
        "flowers": flowers}
