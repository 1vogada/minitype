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
from art_wow import SHADE, SIZES, ridge, sphere_light, stars


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

def _range_line(seed, base, spacing, lo, hi, x0=-9.0, x1=3.0):
    """A mountain range defined everywhere: peaks every `spacing` (jittered)
    with heights lo..hi over base; top(x) -> (y of the crest line, x of
    the peak it belongs to, that peak's height)."""
    peaks = []
    k = 0
    x = x0
    while x < x1:
        j = _hash(k, 1, seed)
        peaks.append((x + (j - 0.5) * spacing * 0.6, spacing * (0.8 + 0.6 * _hash(k, 2, seed)),
                      lo + (hi - lo) * _hash(k, 3, seed)))
        x += spacing
        k += 1

    def top(x):
        best = (0.0, x, 0.0)
        for cx, w, ht in peaks:
            if abs(x - cx) < w:
                h = ht * (1 - abs(x - cx) / w) ** 1.25
                if h > best[0]:
                    best = (h, cx, ht)
        h = best[0] + 0.012 * (fbm(x * 18, 0.3, seed) - 0.5) * min(1.0, best[0] * 10)
        return base - max(0.0, h), best[1], best[2]
    return top


def _bough_pine(cx, base, height, width, tiers, seed):
    """A pine of drooping bough layers: at(x, y) -> None, ("trunk", nx) or
    ("bough", side, v, u, k): side -1 left .. 1 right of the trunk, v 0 at
    a layer's shadowed underside to 1 on its lit top, u 0 at the trunk to 1
    at the bough tips, k the layer (0 at the bottom)."""
    layers = []
    for k in range(tiers):
        f = k / tiers
        tk = 0.15 + 0.79 * f ** 0.92                         # the tips' height, 0..1 up the tree
        wk = width * (1 - tk) ** 0.95 * (0.88 + 0.24 * _hash(k, 7, seed))
        hk = (0.84 / tiers) * 1.9
        layers.append((tk, wk, hk, 0.035 + 0.03 * (1 - f)))

    def at(x, y):
        t = (base - y) / height
        if t < -0.02 or t > 1.0:
            return None
        dx = x - cx
        hit = None
        for k in range(tiers - 1, -1, -1):                   # the higher layer is in front
            tk, wk, hk, droop = layers[k]
            ragged = 1 + 0.16 * (noise(t * 70, k * 3.1, seed) - 0.5) + 0.1 * (noise(t * 22, dx * 9, seed + 5) - 0.5)
            u = abs(dx) / (wk * ragged)
            if u > 1:
                continue
            top = tk - droop * u * u + hk * (1 - u) ** 1.35
            # the underside hangs in tufts of needles
            under = tk - droop * u * u - 0.018 * u * (0.5 + 0.5 * math.sin(dx * 260 + k))
            if under <= t <= top:
                v = (t - under) / max(1e-6, top - under)
                hit = ("bough", -1.0 if dx < 0 else 1.0, v, u, k)
                break
        if hit:
            return hit
        tw = width * 0.05 * (1.15 - t)
        if abs(dx) < tw and t < 0.9:
            return ("trunk", dx / tw)
        return None
    return at


def _ball_light(nx, ny, lx=-0.6, ly=-0.55):
    """0..1 light on a rounded stone at offset (nx, ny) from its middle."""
    z = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
    return clamp(nx * lx + ny * ly + z * math.sqrt(max(0.0, 1 - lx * lx - ly * ly)))


def lone_pine(pal):
    """A lone pine on a mossy rocky point over a still lake at dawn: tall
    pines of drooping, lit bough layers, two ranges of ridged, snow-capped
    mountains with a warm glow between them, a low moon, stars, mist
    lying on the water and the whole scene mirrored in the lake."""
    shore = 0.66
    far = _range_line(4, shore - 0.06, 0.62, 0.16, 0.34)
    near = _range_line(9, shore, 0.48, 0.05, 0.16)
    sky = pal.path("d0 d1 a1 a2 a4 g4 w5 w7")
    far_lit = pal.path("d0 d1 a1 a2 a3 a5 t4")
    near_lit = pal.path("- d0 d1 a1 a2 g2")
    needles = pal.path("- d0 a1 d3 a4 g3 g5 g7")
    stone = pal.path("- x0 x2 x4 e4 t4 t6")
    moss = pal.path("d1 a1 g1 g3 g5")
    glow_x, glow_y = 0.78, shore - 0.12
    moon_x, moon_y, moon_r = 0.3, 0.17, 0.05
    moon_lit = sphere_light(moon_x, moon_y, moon_r, 0.5, -0.3)
    trees = [_bough_pine(1.5, 0.93, 0.7, 0.25, 9, 3), _bough_pine(1.8, 0.95, 0.42, 0.15, 7, 8),
             _bough_pine(1.17, 0.95, 0.3, 0.1, 6, 13)]
    boulders = [(1.12, 0.93, 0.11, 0.06), (1.32, 0.9, 0.15, 0.07), (1.56, 0.89, 0.2, 0.08),
                (1.8, 0.91, 0.17, 0.07), (1.98, 0.92, 0.14, 0.07), (1.02, 0.97, 0.08, 0.04),
                (1.42, 0.97, 0.18, 0.06), (1.7, 0.98, 0.2, 0.06)]

    def glow(x, y):
        return math.exp(-(((x - glow_x) / 0.55) ** 2 + ((y - glow_y) / 0.16) ** 2))

    def rock(x, y):
        """The point: boulders, each round and lit from the upper left, with
        moss on their crowns; soft where they meet the water. -> (rgb,
        alpha) or None."""
        best = None
        for bx, by, rx, ry in boulders:
            wob = 1 + 0.18 * (fbm(x * 14, y * 14, int(bx * 10)) - 0.5)
            d = ((x - bx) / rx) ** 2 + ((y - by) / ry) ** 2
            if d <= wob and (best is None or by > best[1]):        # lower ones in front
                best = (bx, by, rx, ry, d / wob)
        if best is None:
            return None
        bx, by, rx, ry, d = best
        nx, ny = (x - bx) / rx, (y - by) / ry
        lit = clamp(_ball_light(nx, ny) * 0.85 + 0.12 * (fbm(x * 40, y * 40, 3) - 0.5) + 0.05)
        c = stone(lit * 0.95)
        if d > 0.82:
            c = mix(c, pal.rgb("x0"), 0.5)                        # the crack between stones
        mossy = fbm(x * 16, y * 22, 6) + (-ny) * 0.35
        if mossy > 0.62 and ny < 0.3:
            c = moss(clamp(lit * 0.75 + (mossy - 0.62)))
        alpha = clamp(0.55 + (1.02 - y) * 6) if y > 0.95 else 1.0
        return c, alpha

    def mountains(x, y):
        """(rgb, tag) of the two ranges at (x, y), or None in the sky."""
        ny, peak, ht = near(x)
        # the near hills are wooded: a fringe of little spires on the crest
        s = (x * 46) % 1.0
        spire = (1 - abs(s - 0.5) * 2) ** 1.6 * (0.012 + 0.018 * _hash(math.floor(x * 46), 5, 2))
        if y >= ny - spire:
            side = -1 if x < peak else 1
            ridge_ = fbm((x + (y - ny) * 0.8 * side) * 24, y * 3, 9)
            v = clamp(0.5 - max(0.0, y - ny) * 5 + (0.18 if side < 0 else -0.12) + (ridge_ - 0.5) * 0.6)
            c = near_lit(v)
            return c, "mountains"
        fy, peak, ht = far(x)
        base = shore - 0.06
        dip = 1 - 0.65 * math.exp(-((x - glow_x) / 0.32) ** 2)       # a pass where the dawn shows
        fy, ht = base - (base - fy) * dip, ht * dip
        if y >= fy:
            side = -1 if x < peak else 1
            depth = y - fy
            # ridges fan out from each summit, down its faces
            down = max(0.0, y - (base - ht))
            fan = (x - peak) / (down + 0.03)
            gully = fbm(fan * 2.2, down * 6, 4)
            crease = abs(math.sin(fan * 4.5 + gully * 3))
            v = 0.55 + (0.3 if side < 0 else -0.22) + (gully - 0.5) * 0.7 - crease * 0.35 - depth * 1.5
            c = far_lit(clamp(v))
            # snow above a line, reaching further down the gullies
            alt = base - y
            if alt > 0.19 + 0.05 * crease - 0.04 * gully:
                lit_snow = side < 0 and crease < 0.75
                c = pal.rgb(("t8" if lit_snow else "t5") if side < 0 else ("t4" if crease < 0.6 else "a3"))
            haze = clamp((y - (shore - 0.12)) / 0.12) * 0.5
            c = mix(c, pal.rgb("a3"), haze)
            return mix(c, pal.rgb("w5"), glow(x, y) ** 3 * 0.3), "mountains"
        return None

    def sky_at(x, y):
        c = sky(clamp(y / shore * 1.05) ** 1.2 * 0.85 + glow(x, y) * 0.3)
        r = math.hypot(x - moon_x, (y - moon_y) * 1.0)
        c = mix(c, pal.rgb("t5"), math.exp(-((r / 0.14) ** 2)) * 0.35)        # the moon's halo
        streak = soft_clouds([(0.2, 0.33, 0.7, 0.012), (1.1, 0.29, 0.5, 0.01), (-1.2, 0.31, 0.9, 0.012),
                              (0.85, 0.4, 0.35, 0.008), (-2.8, 0.36, 0.8, 0.01)])(x, y)
        if streak:
            c = mix(c, pal.path("a2 e3 w5")(clamp(glow(x, y) * 1.5)), streak * 0.55)
        return c

    def field(x, y):
        for tr in trees:
            hit = tr(x, y)
            if hit:
                if hit[0] == "trunk":
                    return mix(pal.rgb("x1"), pal.rgb("x4"), clamp(-hit[1] * 0.5 + 0.4)), 1.0, True, "tree"
                _, side, v, u, k = hit
                grain = fbm(u * 9 + k, v * 3, k) - 0.5
                light = 0.22 + 0.45 * v ** 1.3 - 0.18 * side + 0.15 * u * (-side) + grain * 0.3
                if side < 0 and u > 0.78 and v > 0.35:
                    light += 0.35                                 # rim light on the dawn side
                return needles(clamp(light)), 1.0, True, "tree"
        rk = rock(x, y)
        if rk:
            return rk[0], rk[1], True, "rock"
        if y < shore:
            m = mountains(x, y)
            if m:
                return m[0], 1.0, False, m[1]
            if math.hypot(x - moon_x, y - moon_y) <= moon_r:
                return pal.path("a4 t5 t8 w9")(moon_lit(x, y)), 1.0, False, "moon"
            mist = math.exp(-((y - shore + 0.015) / 0.025) ** 2) * clamp(fbm(x * 5, y * 12, 7) * 1.6 - 0.4)
            return mix(sky_at(x, y), pal.rgb("t6"), mist * 0.5), 1.0, False, "sky"
        # the lake: everything above mirrored, darker further down, with
        # ripples that catch the glow
        depth = y - shore
        wob = 0.006 * math.sin(y * 260 + 3 * fbm(x * 3, y * 20, 5)) * min(1.0, depth * 12)
        my = shore - depth * 1.25 - 0.004
        c, _, _, tag = field(x + wob, clamp(my, -0.4, shore - 0.001))
        c = mix(c, pal.rgb("d0"), 0.25 + depth * 0.9)
        ripple = math.sin(y * 420 + fbm(x * 6, y * 30, 11) * 8)
        if ripple > 0.82:
            c = mix(c, pal.path("a4 w6")(glow(x, shore)), 0.45 * (1 - depth * 2))
        # the moon's glitter: broken dashes down the water under it
        spread = 0.03 + depth * 0.25
        if abs(x - moon_x) < spread and math.sin(y * 640 + fbm(x * 30, y * 8, 13) * 5) > 0.25:
            c = mix(c, pal.rgb("t7"), clamp(0.8 - depth * 2) * (1 - abs(x - moon_x) / spread))
        mist = math.exp(-((depth - 0.015) / 0.035) ** 2) * clamp(fbm(x * 4, y * 16, 12) * 1.5 - 0.35) * 0.6
        return mix(c, pal.rgb("t5"), mist), 1.0, False, "lake"

    def texts(rows, x_left, cw, unit):
        out = stars(field, rows, x_left, cw, unit, rows * 4, 0.3, [pal.rgb("t8"), pal.rgb("t6"), pal.rgb("w8")],
                    2, chars="..·'+")
        return [s for s in out if math.hypot(x_left + s[0] * cw - moon_x, s[1] * unit - moon_y) > 0.12]

    return scene("pine", field, texts)


# ---------------------------------------------------------------- autumn

# a maple leaf's lobes: (angle from its stem side round, length, half width)
_LOBES = ((math.pi / 2, 1.0, 0.62), (math.pi / 2 + 0.92, 0.92, 0.58), (math.pi / 2 - 0.92, 0.92, 0.58),
          (math.pi / 2 + 1.85, 0.6, 0.5), (math.pi / 2 - 1.85, 0.6, 0.5))


def _maple_reach(a):
    """How far a maple leaf reaches at polar angle a (0 right, pi/2 up
    the leaf, its stem straight down): five pointed lobes, each with two
    side points, toothed all round, and deep notches between them.
    -> (reach, the nearest lobe, angle from its middle)."""
    best, lobe, off = 0.34, 0, math.pi
    for k, (la, ln, w) in enumerate(_LOBES):
        d = math.atan2(math.sin(a - la), math.cos(a - la))
        if abs(d) < abs(off):
            lobe, off = k, d
        if abs(d) < w:
            f = 1 - abs(d) / w
            r = 0.34 + 0.66 * ln * f ** 0.75
            for side in (-1, 1):                              # the lobe's own side points
                g = 1 - abs(d - side * w * 0.45) / (w * 0.14)
                if g > 0:
                    r += 0.14 * ln * g
            best = max(best, r)
    teeth = abs(((a * 17 / math.pi) % 1.0) - 0.5) * 2         # small saw teeth all round
    best += 0.04 * teeth * min(1.0, best - 0.34 + 0.2)
    return best, lobe, off


def _maple(cx, cy, size, ang):
    """A maple leaf at (cx, cy) turned by ang: at(x, y) -> None or (how far
    in 0..1 along its radius, the nearest lobe, angle from it, distance
    from the middle in leaf units, u right, v up the leaf)."""
    ca, sa = math.cos(ang), math.sin(ang)

    def at(x, y):
        dx, dy = (x - cx) / size, (cy - y) / size
        if abs(dx) > 1.25 or abs(dy) > 1.25:
            return None
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        r = math.hypot(u, v)
        reach, lobe, off = _maple_reach(math.atan2(v, u))
        if r > reach:
            return None
        return r / reach, lobe, off, r, u, v
    return at


def leaf(pal):
    """A big maple leaf drifting down in front of an autumn wood: five
    toothed lobes, veined from the stem, turning from gold at its heart
    through orange to red at the tips, folded along its veins and lit from
    the upper left, a few dark spots, and a long curving stalk. Behind it
    trunks stand in a blazing canopy with light slanting through, more
    leaves are falling, and the floor is thick with fallen leaves."""
    cx, cy, size, ang = 1.32, 0.43, 0.41, math.radians(16)
    main = _maple(cx, cy, size, ang)
    ca, sa = math.cos(ang), math.sin(ang)
    flesh = pal.path("w8 w7 w6 a6 a5 e6 e5 e4")
    stalk_c = pal.path("x1 x4 e4 a5 w6")
    leafy = [pal.path("x2 e3 e5 e6 e7"), pal.path("x2 a3 a5 a6 w7"), pal.path("d2 w4 w6 w7 w8"),
             pal.path("x2 x5 e4 a5 a6")]
    bark = pal.path("- x0 d0 d1 d2 d3 a4")
    air = pal.path("- x0 x1 x3 e3 a4 w6")
    floor_y = 0.84

    # the stalk: a curve below the leaf, in leaf units (u right, v up)
    stem_pts = [((1 - t) ** 2 * 0.0 + 2 * (1 - t) * t * 0.0 + t * t * 0.2,
                 (1 - t) ** 2 * -0.12 + 2 * (1 - t) * t * -0.55 + t * t * -0.78) for t in (k / 16 for k in range(17))]

    def stem(x, y):
        """-> across the stalk -1..1 (left to right), or None."""
        dx, dy = (x - cx) / size, (cy - y) / size
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        if not (-0.95 < v < -0.05 and -0.15 < u < 0.35):
            return None
        for k, ((ax, ay), (bx, by)) in enumerate(zip(stem_pts, stem_pts[1:])):
            ex, ey = bx - ax, by - ay
            t = clamp(((u - ax) * ex + (v - ay) * ey) / (ex * ex + ey * ey))
            px, py = u - ax - ex * t, v - ay - ey * t
            half = 0.055 - 0.02 * (k + t) / 16
            if px * px + py * py <= half * half:
                return clamp((px * -ey + py * ex) / math.hypot(ex, ey) / half, -1.0, 1.0)
        return None

    def leaf_colour(hit, x, y):
        k, lobe, off, r, u, v = hit
        la = _LOBES[lobe][0]
        along, across = r * math.cos(off), r * math.sin(off)
        # gold at the heart to red at the tips, redder to the right
        heat = clamp(0.02 + 0.95 * k ** 1.15 + 0.22 * u + 0.3 * (fbm(x * 9, y * 9, 4) - 0.5))
        c = flesh(heat)
        # folded along each lobe's vein: one half catches the light
        lit = 0.55 + (0.22 if off * (1 if la > math.pi / 2 else -1) > 0 else -0.12) - 0.3 * u * 0.5 + 0.18 * v
        lit += 0.2 * (fbm(x * 30, y * 30, 6) - 0.5)
        if lit > 0.62:
            c = mix(c, pal.rgb("w8"), clamp((lit - 0.62) * 1.4) * 0.5)
        else:
            c = mix(c, pal.rgb("e2"), clamp((0.62 - lit) * 1.6) * 0.7)
        # veins: one down each lobe, side veins branching off towards the edge
        vw = 0.024 * (1 - 0.6 * k)
        side = (along - abs(across) * 1.25) % 0.17
        if abs(across) < vw and along > 0:
            c = mix(c, pal.rgb("w8"), 0.75)
        elif min(side, 0.17 - side) < 0.009 and 0.15 < r and k < 0.9:
            c = mix(c, pal.rgb("w7"), 0.45)
        elif r < 0.06:
            c = mix(c, pal.rgb("w8"), 0.6)
        # tar spots
        spot = fbm(x * 34, y * 34, 21)
        if spot > 0.79 and 0.2 < k < 0.85:
            c = mix(pal.rgb("x1"), pal.rgb("e3"), clamp((0.8 - spot) * 12))
        if k > 0.92:
            c = mix(c, pal.rgb("x2"), 0.65)                       # a darker rim
        return c

    # leaves falling, drifting and turning: (x, y, size, angle, colours)
    fall = []
    for i in range(90):
        fx = -7.0 + 9.0 * _hash(i, 1, 31)
        fy = -0.45 + 1.2 * _hash(i, 2, 31)
        if math.hypot(fx - cx, (fy - cy) * 1.0) < size * 1.15 or fy > floor_y - 0.04:
            continue
        fall.append((_maple(fx, fy, 0.05 + 0.04 * _hash(i, 3, 31), 6.28 * _hash(i, 4, 31)),
                     leafy[i % len(leafy)], fx, fy))

    def trunk(x, y):
        """A tree's trunk here: -> (across -1..1, how near 0..1, x) or None."""
        slot = math.floor(x / 0.34)
        for s in (slot - 1, slot, slot + 1):
            near = _hash(s, 1, 77)
            tx = s * 0.34 + 0.17 + 0.24 * (_hash(s, 2, 77) - 0.5)
            w = 0.014 + 0.06 * near ** 2
            lean = (_hash(s, 3, 77) - 0.5) * 0.08
            mid = tx + lean * (floor_y - y) + 0.004 * math.sin(y * 30 + s)
            if abs(x - mid) < w * (1 + 0.25 * clamp(y - floor_y + 0.08) * 12):
                return (x - mid) / w, near, s
        return None

    def canopy(x, y):
        """Leaves overhead: density 0..1 and which colour."""
        dens = (fbm(x * 11, y * 15, 41, 3) + 0.62 - y * 1.1 + 0.15 * (fbm(x * 2, y * 2, 42) - 0.5)
                + 0.22 * (noise(x * 70, y * 100, 44) - 0.5))
        return dens, fbm(x * 2.2, y * 2.2, 43)

    def wood(x, y):
        """(rgb, tag) of the wood behind."""
        yy = max(y, -0.5)
        shaft = clamp(math.sin((x + yy * 0.55) * 9 + fbm(x * 2, 0, 3) * 4) * 1.6 - 0.9)
        glow = math.exp(-(((x - 0.3) / 0.8) ** 2 + ((yy - 0.45) / 0.4) ** 2))
        haze = clamp(0.18 + glow * 0.5 + shaft * 0.22 + 0.2 * (fbm(x * 3, yy * 3, 5) - 0.5))
        edge = floor_y + 0.03 * (fbm(x * 4, 0.5, 8) - 0.5)
        if yy >= edge:
            # the floor: fallen leaves, small and hazy far off, big near
            depth = clamp((yy - floor_y) / (1 - floor_y))
            gx, gy = 0.05 + 0.04 * depth, 0.022 + 0.016 * depth
            ix, iy = math.floor(x / gx), math.floor(yy / gy)
            best = None
            for jx in (ix - 1, ix, ix + 1):
                for jy in (iy - 1, iy, iy + 1):
                    px = (jx + _hash(jx, jy, 51)) * gx
                    py = (jy + _hash(jx, jy, 52)) * gy
                    d = ((x - px) / (gx * 0.75)) ** 2 + ((yy - py) / (gy * 0.8)) ** 2
                    if d < 1 and (best is None or py > best[1]):
                        best = (d, py, _hash(jx, jy, 53))
            if best:
                d, py, h = best
                c = leafy[int(h * 4) % 4](clamp(0.9 - d * 0.6 - (1 - depth) * 0.45 + (h - 0.5) * 0.3))
            else:
                c = pal.rgb("x1")
            c = mix(c, air(haze), clamp(0.4 - depth * 0.6))
            c = mix(c, pal.rgb("x0"), clamp(0.6 - (yy - edge) * 9))           # the shade under the trees
            return c, "ground"
        tr = trunk(x, yy)
        if tr:
            nx, near, s = tr
            light = clamp(0.62 - nx * 0.45 - abs(nx) ** 3 * 0.3) * (0.55 + 0.45 * near)
            light += 0.18 * (noise(nx * 2 + s * 5, yy * 60, 61) - 0.5)       # bark furrows
            c = bark(clamp(light))
            if nx < -0.55 and near > 0.4:
                c = mix(c, pal.rgb("a6"), 0.5)                               # rim lit
            c = mix(c, air(haze), clamp(0.75 - near * 0.95))                  # far ones fade in the haze
            return c, "trees"
        dens, hue = canopy(x, yy)
        if dens > 0.62:
            pick = leafy[0] if hue < 0.45 else leafy[3] if hue < 0.56 else leafy[1] if hue < 0.64 else leafy[2]
            # clumps of leaves: lit at their edges and from above, deep inside
            sun = clamp(0.62 - min(0.3, dens - 0.62) * 1.3 + shaft * 0.2 + 0.6 * (noise(x * 55, yy * 80, 45) - 0.5)
                        - max(0.0, yy - 0.12) * 1.1) * (0.55 + 0.45 * glow + 0.3 * shaft)
            return pick(sun), "trees"
        return air(haze + clamp(0.62 - dens) * 0.4), "wood"

    def field(x, y):
        hit = main(x, y)
        if hit:
            return leaf_colour(hit, x, y), 1.0, True, "leaf"
        st = stem(x, y)
        if st is not None:
            return stalk_c(clamp(0.6 - st * 0.45)), 1.0, True, "leaf"
        for fl, col, fx, fy in fall:
            if abs(x - fx) < 0.09 and abs(y - fy) < 0.09:
                h = fl(x, y)
                if h:
                    c = col(clamp(1.0 - h[0] * 0.45 + 0.2 * h[4]))
                    return (mix(c, pal.rgb("x1"), 0.6) if h[0] > 0.85 else c), 1.0, False, "falling"
        c, tag = wood(x, y)
        if main(x - 0.025, y - 0.035) or stem(x - 0.025, y - 0.035) is not None:
            c = mix(c, pal.ground, 0.45)                          # the leaf's shadow
        return c, 1.0, False, tag

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(7)
        out = []
        for _ in range(rows):
            x, y = rnd.uniform(-3.0, 1.9), rnd.uniform(0.05, 0.8)
            if field(x, y)[3] == "wood":
                out.append((int((x - x_left) / cw), int(y / unit), rnd.choice("·'.,"),
                            rnd.choice([pal.rgb("w8"), pal.rgb("a8"), pal.rgb("t8")]), False))
        return out

    return scene("autumn", field, texts, inks={"leaf": "eawx", "wood": "xeawt", "ground": "xeawd",
                                               "trees": "xeawdg", "falling": "xeawdg"})


# ---------------------------------------------------------------- desert

def _tube(points, radius):
    """A limb of a plant as a tube along a path: (x, y) -> None outside,
    else (across, 0 at the axis to 1 at the skin, signed: < 0 on the left of
    the path's direction; the unit normal (nx, ny) pointing out from the
    axis). Rounded where it ends."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    box = (min(xs) - radius, max(xs) + radius, min(ys) - radius, max(ys) + radius)
    segs = list(zip(points, points[1:]))

    def at(x, y):
        if not (box[0] <= x <= box[1] and box[2] <= y <= box[3]):
            return None
        best = None
        for (ax, ay), (bx, by) in segs:
            dx, dy = bx - ax, by - ay
            ln = dx * dx + dy * dy
            t = clamp(((x - ax) * dx + (y - ay) * dy) / ln) if ln else 0.0
            px, py = x - (ax + dx * t), y - (ay + dy * t)
            d = math.hypot(px, py)
            if best is None or d < best[0]:
                side = 1 if dx * py - dy * px > 0 else -1
                best = (d, px, py, side)
        d, px, py, side = best
        if d > radius:
            return None
        n = (px / d, py / d) if d else (0.0, 0.0)
        return side * d / radius, n
    return at


def _curve(p0, p1, p2, n=10):
    """Points along a quadratic bezier."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (k / n for k in range(n + 1))]


def cactus(pal):
    """A tall saguaro at golden hour: a ribbed trunk and two arms that
    curve out and up, shaded round as tubes and lit from the low sun on the
    left (a warm rim on that side, the far side in cool shade, never
    black), blossoms on its crown, spines catching the light; it stands in
    a little mound of sand and throws a long shadow away from the sun.
    Mesas on the horizon, dunes rippling away."""
    hz = 0.7
    sx, sy, sr = 0.55, 0.62, 0.09
    sky = pal.path("x1 e4 a4 a6")
    mesas = [(-0.1, 0.42, 0.13), (0.95, 0.3, 0.08), (-1.3, 0.5, 0.16), (-2.4, 0.35, 0.1)]
    tx, tw, top, foot = 1.36, 0.068, 0.08, 0.92
    aw = tw * 0.72
    limbs = [_tube([(tx, foot), (tx, top + tw)], tw)]
    for fy, side, reach, rise in ((0.58, -1, 0.15, 0.24), (0.44, 1, 0.13, 0.28)):
        ax = tx + side * reach
        elbow = _curve((tx, fy), (ax, fy + 0.012), (ax, fy - 0.07))
        limbs.append(_tube(elbow + [(ax, fy - rise + aw)], aw))
    crown = [(tx - 0.03, top + 0.005), (tx + 0.02, top - 0.002), (tx - 0.07, 0.38),
             (tx + 0.13 - 0.02, 0.165)]
    # the light: low, from the sun on the left, a little towards us
    lx, ly, lz = -0.86, -0.12, 0.5
    flesh = pal.path("g0 g1 g2 g4 g6 w6 w8")

    def plant(x, y):
        """(colour) of the saguaro at (x, y), or None."""
        for limb in limbs:
            got = limb(x, y)
            if got:
                break
        else:
            return None
        u, (nx, ny) = got
        depth = math.sqrt(max(0.0, 1 - u * u))          # how much it faces us
        k = abs(u)
        lit = clamp((nx * lx + ny * ly) * k + depth * lz)
        theta = math.asin(max(-1.0, min(1.0, u)))
        rib = math.cos(theta * 5)                       # ribs run along the limb, a few cells wide
        b = 0.08 + 0.9 * lit ** 1.3                     # never black: sky light in the shade
        b *= 0.74 + 0.26 * rib
        c = flesh(clamp(b))
        if k > 0.78 and nx * lx + ny * ly > 0.3:         # the sun catching its edge
            c = mix(c, pal.rgb("w7"), (k - 0.78) / 0.22 * 0.6)
        return c

    def field(x, y):
        for bx, by in crown:
            if (x - bx) ** 2 + ((y - by) * 0.6) ** 2 < 0.012 ** 2:
                return pal.rgb("w9"), 1.0, True, "cactus"
        c = plant(x, y)
        if c is not None:
            return c, 1.0, True, "cactus"
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
        # the little mound it stands in: sand heaped round its foot
        mound = math.exp(-((x - tx) / 0.11) ** 2 - ((y - foot) / 0.025) ** 2)
        c = pal.path("a6 a4 x4 x1 -")(clamp(t * 0.9 + ripple * 0.06 - mound * 0.25))
        if ripple > 0.75 and t > 0.1:
            c = mix(c, pal.rgb("w8"), 0.35)
        # its long shadow, away from the sun, softening as it goes
        along = x - tx
        if along > -tw:
            sy0 = foot + 0.012 + along * 0.025          # a low sun: long and flat
            width = 0.014 + along * 0.012
            strength = math.exp(-((y - sy0) / width) ** 4) * clamp(1.05 - along / 0.75) * 0.85
            c = mix(c, pal.path("x1 -")(0.45), clamp(strength))
        c = mix(c, pal.rgb("x1"), math.exp(-((x - tx) / 0.05) ** 2 - ((y - foot) / 0.012) ** 2) * 0.5)
        return c, 1.0, False, "sand"

    def texts(rows, x_left, cw, unit):
        out = stars(field, rows, x_left, cw, unit, rows * 2, 0.25, [pal.rgb("t8")], 6, chars="..·")
        rnd = random.Random(3)
        for _ in range(rows):                      # spines catching the light on the sunny side
            y = rnd.uniform(top + 0.05, 0.92)
            x = tx - tw * rnd.uniform(0.86, 0.98)
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
