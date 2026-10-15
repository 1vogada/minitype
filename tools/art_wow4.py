"""More "wow" pictures (see art_wow.py): the screen, colour and night
themes - matrix, amber, paper, high contrast, rainbow, party, glitch,
bubbly, aurora, synthwave, deep sea, phosphor, vaporwave, summit."""

import math
import random

import art_combined
from art_combined import mix
from art_wow import SHADE, SIZES, pine, ridge, sphere_light, stars
from art_wow2 import clamp, fbm, noise, scene, soft_clouds
from art_wow3 import bezier, poly, strokes


def _col(x, x_left, cw):
    return int((x - x_left) / cw)


# ---------------------------------------------------------------- matrix

def rain(pal):
    """Digital rain: columns of glyphs falling at different speeds, bright
    heads fading into long tails, deeper columns dimmer, a glowing figure
    of light where they're thickest."""
    def field(x, y):
        glow = math.exp(-((x - 1.35) / 0.35) ** 2 - ((y - 0.5) / 0.5) ** 2)
        floor = y > 0.85 and (abs(math.sin((x - 1.3) / (y - 0.6) * 4)) < 0.08 or abs(math.sin(y * 60 / (y - 0.6))) < 0.1)
        c = pal.path("- d1 d4")(glow * 0.6 + (0.25 if floor else 0))
        return c, 1.0, abs(x - 1.35) < 0.3 and 0.12 < y < 0.88, "void"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(42)
        out = []
        glyphs = "0123456789$+-*/=<>|:;ZXJKLMWQ#@%&"
        cols = int(5.2 / cw)
        for c in range(cols):
            x = x_left + c * cw
            if rnd.random() < 0.35:
                continue
            head = rnd.uniform(-0.2, 1.1)
            length = rnd.uniform(0.2, 0.8)
            bright = 0.5 + 0.5 * math.exp(-((x - 1.35) / 0.4) ** 2)
            for r in range(rows):
                y = r * unit
                t = (head - y) / length
                if 0 <= t <= 1:
                    tone = "t9" if t < 0.03 else ("g8" if t < 0.2 else ("g6" if t < 0.5 else "g4"))
                    if bright < 0.7 and tone in ("g8", "g6"):
                        tone = "g4"
                    out.append((c, r, rnd.choice(glyphs), pal.rgb(tone), abs(x - 1.35) < 0.3 and 0.12 < y < 0.88))
        return out

    return scene("matrix", field, texts)


# ---------------------------------------------------------------- amber

def monitor(pal):
    """A piece of amber with a small dinosaur trapped inside, lit from
    behind: a glowing core, cloudy inclusions, a bright rim, warm falloff
    into a dark room."""
    ax, ay, ar = 1.25, 0.5, 0.28

    def in_amber(x, y):
        """The polished stone: a rounded blob with an irregular outline."""
        u, v = (x - ax) / ar, (y - ay) / (ar * 1.32)
        w = 0.06 * fbm(x * 15, y * 15, 3) + 0.03 * math.sin(y * 26 + x * 5)
        return u * u + v * v <= 1 + w

    def rex(x, y):
        """A little theropod caught in the resin: body, tail, neck, head,
        two legs. True inside the silhouette, None outside it."""
        # the animal fills most of the stone, a bit below its middle
        bx, by = ax - 0.01, ay + 0.015
        u, v = (x - bx) / 0.2, (y - by) / 0.2
        body = (u / 0.85) ** 2 + ((v + 0.05) / 0.4) ** 2 <= 1
        taper = clamp((u + 2.2) / 1.5)
        tail = -2.2 < u < -0.7 and abs(v + 0.05 - (u + 0.7) * 0.18) < 0.17 * taper
        neck = -0.6 < u < 0.2 and -0.85 < v < -0.2 and abs(u - 0.05 + (v + 0.5) * 0.55) < 0.19
        head = ((u - 0.36) / 0.3) ** 2 + ((v + 0.94) / 0.19) ** 2 <= 1
        snout = 0.42 < u < 0.86 and -1.05 < v < -0.82
        leg1 = -0.46 < u < -0.18 and 0.15 < v < 0.95
        leg2 = 0.14 < u < 0.42 and 0.15 < v < 0.88
        foot1 = -0.6 < u < -0.12 and 0.9 < v < 1.06
        foot2 = 0.02 < u < 0.5 and 0.82 < v < 0.98
        arm = 0.22 < u < 0.55 and -0.3 < v < -0.02
        return body or tail or neck or head or snout or leg1 or leg2 or foot1 or foot2 or arm

    top = 0.872                                         # the table's surface, back edge

    def stone(x, y):
        """The amber's colour and tag at (x, y), or None outside it."""
        if not in_amber(x, y):
            return None
        u, v = (x - ax) / ar, (y - ay) / (ar * 1.32)
        r = math.hypot(u, v)
        # the stone is lit from behind: brightest in the middle
        core = clamp(1.0 - r * 0.8)
        cloudy = fbm(x * 9, y * 9, 2) * 0.3 + fbm(x * 24, y * 24, 5) * 0.12
        t = clamp(core * 0.95 + cloudy * 0.35 + 0.15)
        if rex(x, y):
            # the animal shows as a darker amber: lit through where the
            # resin is thin, deeper where the body is thick
            return pal.path("x1 x4 g4 w6")(clamp(0.05 + core * 0.55)), "rex"
        # no g6 in the path: the mix either side of it comes out olive
        c = pal.path("x1 x4 w6 w8 w9")(clamp(t * 1.35))
        if r > 0.86:                                    # the polished edge
            return pal.path("w6 w8 w9")(clamp(1 - (r - 0.86) * 3)), "amber"
        return c, "amber"

    def field(x, y):
        got = stone(x, y)
        if got:
            return got[0], 1.0, True, got[1]
        halo = math.exp(-(((x - ax) / 0.62) ** 2 + ((y - ay) / 0.55) ** 2))
        if y < top:                                     # a warm halo, then the dark room
            return pal.path("- x0 x1 w2")(clamp(halo * 0.8)), 1.0, False, "room"
        # dark polished wood: long grain, a warm pool of light round the
        # stone, its mirror image below it, softening with distance
        d = (y - top) / (1 - top)                       # 0 at the back .. 1 at the front
        grain = fbm(x * 2.5, y * 70, 2) * 0.6 + fbm(x * 9, y * 160, 7) * 0.4
        pool_w = math.exp(-((x - ax) / 0.9) ** 2)          # the wood shows more near the light
        wood = pal.path("- w0 t0 t1")(clamp(0.16 + (grain - 0.5) * (0.12 + 0.5 * pool_w) + pool_w * 0.25 - d * 0.06))
        pool = math.exp(-((x - ax) / (0.42 + d * 0.2)) ** 2 - (d / 0.9) ** 2)
        c = mix(wood, pal.rgb("w4"), pool * 0.45)
        if y - top < 0.006:                              # the back edge catches the glow
            c = mix(c, pal.rgb("w6"), 0.25 + 0.6 * math.exp(-((x - ax) / 0.5) ** 2))
        ripple = 0.004 * math.sin(y * 300 + x * 4) * d    # the polish isn't perfect
        mirror = stone(x + ripple, 2 * top - y)
        if mirror:
            c = mix(c, mirror[0], 0.62 - d * 0.35 - grain * 0.12)
        if y - top < 0.008 and abs(x - ax) < ar * 0.55:  # the stone's contact shadow
            c = mix(c, pal.ground, 0.6)
        return c, 1.0, False, "table"

    def texts(rows, x_left, cw, unit):
        # specks of dust and bubbles caught in the resin
        rnd = random.Random(13)
        out = []
        for _ in range(70):
            ang, rad = rnd.uniform(0, 6.283), rnd.uniform(0, 0.95)
            x = ax + math.cos(ang) * rad * ar * 0.92
            y = ay + math.sin(ang) * rad * ar * 1.24
            if in_amber(x, y) and not rex(x, y):
                out.append((_col(x, x_left, cw), int(y / unit), rnd.choice(".,'`"),
                            rnd.choice([pal.rgb("w8"), pal.rgb("a8"), pal.rgb("x4")]), True))
        return out

    return scene("amber", field, texts, inks={"amber": "xwt", "rex": "xwt", "room": "xw", "table": "tw"})


# ---------------------------------------------------------------- paper

def plane(pal):
    """A paper plane gliding across a big blue sky, its dashed trail
    looping behind, paper-cut clouds in layers below."""
    px, py = 1.3, 0.35
    body = poly([(px + 0.25, py - 0.06), (px - 0.22, py - 0.12), (px - 0.12, py + 0.02)])
    wing = poly([(px + 0.25, py - 0.06), (px - 0.12, py + 0.02), (px - 0.18, py + 0.12)])
    fold = poly([(px + 0.25, py - 0.06), (px - 0.12, py + 0.02), (px - 0.06, py + 0.05)])
    layers = [(0.62, "d1", 0.05), (0.74, "d4", 0.06), (0.86, "d6", 0.07)]

    def field(x, y):
        if fold(x, y):
            return pal.rgb("d6"), 1.0, True, "plane"
        if body(x, y):
            return pal.rgb("t1"), 1.0, True, "plane"
        if wing(x, y):
            return pal.rgb("d1"), 1.0, True, "plane"
        for base, col, amp in layers:
            edge = base - amp * (0.6 + 0.4 * math.sin(x * 9 + base * 30)) * abs(math.sin(x * 4.5 + base * 10)) ** 0.5
            if y > edge:
                shadow = y - edge < 0.012
                return (pal.rgb("d4") if shadow and col == "d1" else pal.rgb(col)), 1.0, False, "cloud"
        return pal.path("a6 a4 a1")(clamp(y * 1.4)), 1.0, False, "sky"

    def lines(rows):
        pts = []
        for k in range(120):
            t = k / 119
            x = px - 0.2 - t * 2.6
            y = py + 0.05 + 0.12 * math.sin(t * 9) * (1 - t * 0.3) + t * 0.1
            pts.append((x, y))
        dashes = [pts[i:i + 4] for i in range(0, len(pts) - 4, 7)]
        return [(d, pal.rgb("t1"), False, None) for d in dashes]

    return scene("paper", field, None, lines, inks={"sky": "a", "cloud": "dt", "plane": "dt"})


# ---------------------------------------------------------------- high contrast

def bolt(pal):
    """A lightning strike: a jagged white bolt with branches from a dark
    storm cloud, the cloud lit from inside, rain slanting down."""
    rnd = random.Random(9)
    main, x, y = [], 1.3, 0.22
    while y < 0.95:
        main.append((x, y))
        x += rnd.uniform(-0.07, 0.07)
        y += rnd.uniform(0.04, 0.08)
    main.append((x, 0.97))
    branches = [main]
    for k in (2, 5, 8):
        if k < len(main):
            bx, by = main[k]
            br = [(bx, by)]
            for _ in range(4):
                bx += rnd.choice((-1, 1)) * rnd.uniform(0.03, 0.08)
                by += rnd.uniform(0.03, 0.06)
                br.append((bx, by))
            branches.append(br)
    core = strokes([(b, 0.012, 0.006) for b in branches])
    halo = strokes([(b, 0.04, 0.02) for b in branches])

    def field(x, y):
        if core(x, y) is not None:
            return pal.rgb("t9"), 1.0, True, "bolt"
        h = halo(x, y)
        cloud = fbm(x * 3, y * 6, 4, 4) - y * 0.9
        if cloud > 0.15:
            lit = math.exp(-((x - 1.3) / 0.4) ** 2)
            return pal.path("- d1 d4 d6")(clamp((cloud - 0.15) * 2 + lit * 0.5)), 1.0, False, "cloud"
        if h is not None:
            return pal.rgb("a6"), 1.0, True, "bolt"
        if y > 0.94:
            return pal.path("d1 -")(clamp((y - 0.94) * 15)), 1.0, False, "ground"
        flash = math.exp(-((x - 1.3) / 0.6) ** 2) * 0.35
        return pal.path("- d1")(flash), 1.0, False, "sky"

    def lines(rows):
        rnd2 = random.Random(3)
        out = []
        for _ in range(rows * 4):
            x, y = rnd2.uniform(-3.2, 1.9), rnd2.uniform(0.3, 0.9)
            out.append(([(x, y), (x - 0.02, y + 0.05)], pal.rgb("d6"), False, None))
        return out

    return scene("high contrast", field, None, lines)


# ---------------------------------------------------------------- rainbow

def _puffs(spec):
    """Cumulus clouds: spec [(cx, base, [(dx, dy, r), ...])]; at(x, y) ->
    None outside, else (how high up the cloud 0..1, light 0..1)."""
    def at(x, y):
        for cx, base, balls in spec:
            if y > base:
                continue
            best = None
            for dx, dy, r in balls:
                bx, by = cx + dx, base - dy
                d = math.hypot(x - bx, y - by)
                if d <= r:
                    # lit from the upper right: the side of each ball facing it
                    lit = clamp(0.55 + ((x - bx) * 0.6 - (y - by) * 0.9) / r * 0.6)
                    best = max(best or 0.0, lit)
            if best is not None:
                return clamp((base - y) / 0.12), best
        return None
    return at


def rainbow(pal):
    """A bold rainbow after the rain: a blue sky washed clean, the sun
    breaking through, sunlit cumulus, every band of the spectrum arcing
    over rolling green hills full of flowers, sparkles in the air."""
    cx, cy, outer, band = 1.22, 0.92, 0.74, 0.034
    bands = ["e6", "x6", "w6", "g6", "d3", "a5"]
    sun = (1.78, 0.1, 0.07)
    clouds = _puffs([
        (-0.55, 0.3, [(0, 0.04, 0.07), (0.09, 0.06, 0.08), (0.19, 0.03, 0.06), (-0.1, 0.02, 0.05), (0.28, 0.01, 0.04)]),
        (0.35, 0.2, [(0, 0.03, 0.05), (0.07, 0.05, 0.06), (0.15, 0.025, 0.045), (-0.07, 0.015, 0.035)]),
        (1.55, 0.2, [(0, 0.03, 0.045), (0.07, 0.05, 0.06), (0.15, 0.03, 0.05), (-0.06, 0.015, 0.03)]),
        (0.62, 0.45, [(0, 0.02, 0.03), (0.05, 0.03, 0.04), (0.1, 0.015, 0.03)]),
        (-1.7, 0.22, [(0, 0.03, 0.06), (0.08, 0.05, 0.07), (0.17, 0.02, 0.05)]),
    ])

    def far(x):
        return 0.7 + 0.03 * math.sin(x * 3.1 + 1.0) + 0.015 * math.sin(x * 7.3)

    def near(x):
        return 0.8 + 0.045 * math.sin(x * 2.4 + 0.3) + 0.02 * math.sin(x * 5.9 + 2.0)

    def front(x):
        return 0.9 + 0.04 * math.sin(x * 3.3 + 2.2) + 0.012 * math.sin(x * 9.0)

    def grass(x, y, top, ramp, seed):
        k = y - top
        c = pal.path(ramp)(clamp(k * 7 + (noise(x * 70, y * 40, seed) - 0.5) * 0.35))
        slope = top - [far, near, front][seed](x + 0.01)
        return mix(c, pal.rgb("w7"), clamp(slope * 30) * 0.35 * clamp(1 - k * 10))  # sunny side

    def field(x, y):
        for top, ramp, seed in ((front, "g8 g6 g5 g3", 2), (near, "g7 g5 g4 g2", 1), (far, "g6 g5 g4 g3", 0)):
            if y >= top(x):
                c = grass(x, y, top(x), ramp, seed)
                return (mix(c, pal.rgb("d8"), 0.3) if seed == 0 else c), 1.0, False, "hills"   # haze on the far hills
        r = math.hypot(x - cx, y - cy)
        k = (outer - r) / band
        if 0 <= k < len(bands):
            c = pal.rgb(bands[int(k)])
            fade = clamp((near(x) - y) / 0.15)                  # thinning out into the haze at its feet
            sky = pal.path("d4 d5 d6 d8 d9")(clamp(y / 0.75))
            return mix(sky, c, 0.35 + 0.65 * fade), 1.0, True, "rainbow"
        c = pal.path("d4 d5 d6 d8 d9")(clamp(y / 0.75))
        if r < outer - band * len(bands):
            c = mix(c, pal.rgb("d9"), 0.3)                        # brighter inside the bow
        d = math.hypot(x - sun[0], y - sun[1])
        c = mix(c, pal.rgb("t9"), clamp(math.exp(-((d - sun[2]) / 0.12) ** 2) * 0.7 + (d < sun[2])))
        if sun[2] < d < 0.45:
            ang = math.atan2(y - sun[1], x - sun[0])
            c = mix(c, pal.rgb("w9"), (math.sin(ang * 12) > 0.6) * 0.25 * (1 - d / 0.45))   # sun rays
        cl = clouds(x, y)
        if cl:
            h, lit = cl
            shade = pal.path("d6 d8 t8 t9 t9")(clamp(lit * 0.7 + h * 0.45))
            return shade, 1.0, False, "cloud"
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(11)
        out = []
        flowers = [pal.rgb(k) for k in ("e7", "w8", "a7", "t9", "x7", "a8")]
        for _ in range(rows * 24):
            x, y = rnd.uniform(-3.1, 1.9), rnd.uniform(0.72, 1.0)
            tag = field(x, y)[3]
            if tag == "hills" and y > near(x) + 0.02:
                out.append((_col(x, x_left, cw), int(y / unit), rnd.choice("*'.o*"), rnd.choice(flowers), False))
        for _ in range(rows * 2):
            x, y = rnd.uniform(-3.1, 1.9), rnd.uniform(0.05, 0.6)
            if field(x, y)[3] == "sky":
                out.append((_col(x, x_left, cw), int(y / unit), rnd.choice("+·*"),
                            rnd.choice([pal.rgb("t9"), pal.rgb("w9")]), False))
        for x, y in ((0.0, 0.38), (0.07, 0.35), (0.12, 0.4)):
            out.append((_col(x, x_left, cw), int(y / unit), "v", pal.rgb("d2"), False))
        return out

    return scene("rainbow", field, texts, inks={"sky": "dtw", "cloud": "td", "hills": "gwd"})


# ---------------------------------------------------------------- party

def _scatter(n, seed, x0, x1, y0, y1, cell=(0.014, 0.022)):
    """n small pieces (confetti) on a grid: {(i, j): (index, rnd 0..1)}."""
    rnd = random.Random(seed)
    out = {}
    for k in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        out[(math.floor(x / cell[0]), math.floor(y / cell[1]))] = (k, rnd.random())
    return out


def party(pal):
    """A party hall in pink: a bunch of shiny balloons tied to a present,
    curly strings, streamers and confetti in the air, bunting across the
    top, bokeh lights in a soft pink haze and a glossy floor mirroring
    it all."""
    from art_wow3 import limbs
    fl = 0.8                                                   # where the floor starts
    # (x, y, radius, colour letter); first is nearest
    balloons = [(1.22, 0.42, 0.075, "g"), (1.5, 0.36, 0.08, "x"), (1.06, 0.27, 0.085, "a"),
                (1.36, 0.2, 0.08, "w"), (1.68, 0.2, 0.075, "a"), (1.78, 0.46, 0.07, "w"),
                (0.9, 0.48, 0.065, "a"), (1.6, 0.6, 0.06, "g"), (1.2, 0.11, 0.06, "x"),
                (1.88, 0.12, 0.06, "g")]
    drift = [(0.35, 0.22, 0.045, "w"), (-0.2, 0.12, 0.04, "a"), (-1.1, 0.3, 0.04, "x"),
             (-2.0, 0.16, 0.045, "g"), (-2.7, 0.34, 0.035, "w"), (0.0, 0.5, 0.035, "g")]
    shade = {L: pal.path(f"{L}0 {L}2 {L}4 {L}6 {L}8 t6") for L in "agxw"}
    box = (1.31, 0.76, 0.11, 0.12)                             # the present: centre x, top, half width, height
    knot = (box[0], box[1] - 0.025)

    # strings: curly, down to the bow on the present (or hanging free)
    rnd = random.Random(12)
    spaths = []
    for bx, by, br, _ in balloons + drift:
        top = (bx, by + br * 1.32)
        tied = bx > 0.8
        end = (knot[0] + rnd.uniform(-0.02, 0.02), knot[1]) if tied else (bx + rnd.uniform(-0.05, 0.05), by + 0.3)
        ph, amp = rnd.uniform(0, 6), rnd.uniform(0.006, 0.012)
        pts = []
        for j in range(41):
            s = j / 40
            curl = amp * math.sin(s * 34 + ph) * (1 - s * 0.6) if s < 0.45 else amp * 0.4 * math.sin(s * 12 + ph)
            pts.append((top[0] + (end[0] - top[0]) * s ** 1.3 + curl, top[1] + (end[1] - top[1]) * s))
        spaths.append((pts, 0.0035, 0.003))
    strings = limbs(spaths)

    # streamers spiralling down from the ceiling
    tpaths, tcol = [], []
    for k in range(11):
        x0, ln = rnd.uniform(-3.2, 1.9), rnd.uniform(0.25, 0.6)
        ph, dx = rnd.uniform(0, 6), rnd.uniform(-0.15, 0.15)
        tpaths.append(([(x0 + dx * s + 0.03 * math.sin(s * 16 + ph), s * ln) for s in (j / 30 for j in range(31))],
                       0.008, 0.006))
        tcol.append("agxw"[k % 4])
    streamers = limbs(tpaths)
    confetti = _scatter(380, 3, -3.2, 1.9, 0.0, fl)
    bokeh = [(rnd.uniform(-3.2, 1.9), rnd.uniform(0.3, 0.75), rnd.uniform(0.03, 0.07), rnd.choice("agwx"))
             for _ in range(30)]
    sky = pal.path("- x0 x1 x2 a2 a4 g5")

    def balloon(x, y, group):
        for bx, by, br, L in group:
            u, v = (x - bx) / br, (y - by) / (br * 1.18)
            u /= 1 - 0.14 * max(0.0, v)                        # narrower at the bottom
            d2 = u * u + v * v
            if d2 <= 1:
                z = math.sqrt(1 - d2)
                light = clamp(-u * 0.5 - v * 0.55 + z * 0.65)
                if (u + 0.38) ** 2 + ((v + 0.45) * 1.4) ** 2 < 0.035:
                    return pal.rgb("t9")                       # the shine
                if (u + 0.15) ** 2 * 3 + (v + 0.62) ** 2 < 0.02:
                    return pal.rgb("t6")
                if d2 > 0.7 and u + v > 0.75:
                    light = clamp(light + 0.3)                 # light bouncing back off the room
                return shade[L](light * 0.92)
            if abs(x - bx) < br * 0.13 * (1 - (y - by - br * 1.18) / (br * 0.16)) + 0.004 \
                    and 0 <= y - by - br * 1.18 < br * 0.16:
                return shade[L](0.35)                          # the knot
        return None

    def present(x, y):
        cx, top, hw, h = box
        if abs(x - cx) <= hw and top <= y <= top + h:
            face = (x - cx) / hw
            if abs(x - cx) < 0.014:
                return pal.path("a2 a5 a7")(0.6 - face * 0.3)   # the ribbon
            if y < top + 0.022:
                return pal.path("w4 w6 w8")(0.8 + face * 0.2) if abs(y - top - 0.011) > 0.005 else pal.rgb("a6")
            return pal.path("w1 w3 w5 w7")(clamp(0.7 - face * 0.35 - (y - top) * 2))
        for side in (-1, 1):                                   # the bow: two loops
            if math.hypot((x - cx - side * 0.03) / 0.032, (y - top + 0.012) / 0.024) < 1:
                return pal.path("a3 a6 a8")(0.6 - side * 0.3)
        return None

    def room(x, y):
        c = sky(clamp(0.25 + y * 0.85))
        glow = math.exp(-((y - 0.72) / 0.2) ** 2) * math.exp(-((x - 1.3) / 1.4) ** 2)
        c = mix(c, pal.rgb("g6"), glow * 0.45)
        for bx, by, br, L in bokeh:
            d = math.hypot(x - bx, y - by) / br
            if d < 1:
                c = mix(c, pal.rgb(L + "6"), 0.28 + (0.18 if d > 0.8 else 0))
        return c

    def air(x, y):
        """Bunting, streamers and confetti, or None."""
        sag = 0.03 + 0.07 * math.sin(math.pi * (((x + 3.2) / 0.85) % 1))
        if abs(y - sag) < 0.005:
            return pal.rgb("t5")
        f = (x + 3.2) / 0.085
        if 0 < y - sag < 0.085 * max(0.0, 1 - abs(f % 1 - 0.5) * 2.2) ** 0.8:
            L = "agwx"[int(f) % 4]
            return shade[L](0.75 - (y - sag) * 6)
        hit = streamers(x, y)
        if hit:
            t, nx, ny, k = hit
            return shade[tcol[k]](clamp(0.45 + nx * -0.4 + 0.25 * math.sin(t * 40)))
        piece = confetti.get((math.floor(x / 0.014), math.floor(y / 0.022)))
        if piece:
            fx, fy = (x / 0.014) % 1, (y / 0.022) % 1
            if (fx < 0.95 and fy < 0.3) if piece[0] % 2 else (fx < 0.5 and fy < 0.55):
                return shade["agwa"[piece[0] % 4]](0.6 + piece[1] * 0.35)
        return None

    def field(x, y):
        c = balloon(x, y, balloons)
        if c:
            return c, 1.0, True, "balloon"
        if present(x, y):
            return present(x, y), 1.0, True, "present"
        if strings(x, y) and y < fl + 0.1:
            return pal.rgb("t7" if x > 0.8 else "t4"), 1.0, x > 0.8, "string" if x > 0.8 else "air"
        c = balloon(x, y, drift)
        if c:
            return c, 1.0, False, "air"
        if y >= fl:
            t = (y - fl) / (1 - fl)
            ripple = 0.006 * math.sin(x * 90 + y * 40)
            my = fl - (y - fl) * 2.2 + ripple                        # mirrored, a little rippled
            u = (x - 1.3) / (t + 0.12)
            seam = abs((u * 2.2) % 1 - 0.5) > 0.45 or abs(((1 / (t + 0.12)) * 1.6) % 1 - 0.5) > 0.43
            base = pal.path("x0 x1 x2 x3 a3 a5")(clamp(0.45 - t * 0.35 + (0.12 if seam else 0)
                                                       + math.exp(-((x - 1.3) / 0.7) ** 2) * 0.3 * (1 - t)))
            mb = box[1] + box[3]
            r = present(x, 2 * mb - y + ripple) if y > mb else None
            r = r or balloon(x, my, balloons + drift)
            if r:
                return mix(base, r, 0.6 - t * 0.3), 1.0, False, "floor"
            return mix(base, room(x, my), 0.35 * (1 - t)), 1.0, False, "floor"
        a = air(x, y)
        if a:
            return a, 1.0, False, "air"
        return room(x, y), 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        rnd2 = random.Random(19)
        out = []
        for _ in range(rows * 3):
            x, y = rnd2.uniform(-3, 1.9), rnd2.uniform(0.05, 0.99)
            tag = field(x, y)[3]
            if tag in ("room", "floor"):
                out.append((_col(x, x_left, cw), int(y / unit), rnd2.choice("+*·'" if tag == "room" else "+·*."),
                            rnd2.choice([pal.rgb("a8"), pal.rgb("w9"), pal.rgb("t9"), pal.rgb("g8")]), False))
        return out

    return scene("party", field, texts, inks={"balloon": "agxwt", "room": "xag", "floor": "xagwt",
                                              "present": "wat", "air": "agxwt", "string": "t"})


# ---------------------------------------------------------------- glitch

def glitch(pal):
    """A glitched sunset on a cracked screen: the picture sliced into bands
    that slip sideways, colour channels split apart, static, dead pixels."""
    rnd = random.Random(23)
    slips = {}
    for _ in range(14):
        y0 = rnd.uniform(0, 1)
        slips[(round(y0, 2))] = (rnd.uniform(0.008, 0.04), rnd.uniform(-0.25, 0.25))

    def base(x, y):
        sx, sy, sr = 1.3, 0.5, 0.25
        d = math.hypot(x - sx, y - sy)
        if y > 0.62:
            grid = abs(math.sin((x - sx) / (y - 0.55) * 3)) < 0.1 or abs(math.sin(1 / (y - 0.55) * 3)) < 0.15
            return (pal.rgb("a6") if grid else pal.path("x1 -")((y - 0.62) * 3)), False
        if d <= sr and not (y > sy and math.sin(y * 120) > 0.5):
            return pal.path("w8 a6 e6")(clamp((y - sy + sr) / (2 * sr))), True
        return pal.path("- x1 e1 a4")(clamp(y * 1.4)), False

    def field(x, y):
        shift = 0.0
        for y0, (h, dx) in slips.items():
            if y0 <= y < y0 + h:
                shift = dx
        c, foc = base(x + shift, y)
        r, _ = base(x + shift + 0.025, y)
        g, _ = base(x + shift - 0.025, y)
        if r != c:
            c = mix(c, pal.rgb("e6"), 0.6)
        elif g != c:
            c = mix(c, pal.rgb("g6"), 0.5)
        if noise(x * 200, y * 60) > 0.93:
            c = pal.rgb("t8")
        return c, 1.0, foc or (abs(x - 1.3) < 0.3 and 0.25 < y < 0.75), "screen"

    return scene("glitch", field)


# ---------------------------------------------------------------- bubbly

def _buckets(discs, cell=0.12):
    """Discs (x, y, r, ...) by the grid squares they touch, so a field
    with hundreds of them only tests the few nearby: at(x, y) -> list."""
    grid = {}
    for dsc in discs:
        x, y, r = dsc[:3]
        for i in range(math.floor((x - r) / cell), math.floor((x + r) / cell) + 1):
            for j in range(math.floor((y - r) / cell), math.floor((y + r) / cell) + 1):
                grid.setdefault((i, j), []).append(dsc)
    return lambda x, y: grid.get((math.floor(x / cell), math.floor(y / cell)), ())


def bubbles(pal):
    """Soap bubbles drifting up through a rosy dusk: crisp bright rims,
    thin-film swirls of pink, violet and gold on their skins, the room
    behind seen upside down and darker through each one, a hard window
    glint and a soft second reflection; far bubbles small and hazy, near
    ones sharp, out-of-focus discs of light deep behind. No green."""
    rnd = random.Random(29)
    # (x, y, r, depth 0 far .. 1 near); the big ones are the subject
    big = [(1.3, 0.45, 0.24, 1.0), (1.72, 0.25, 0.12, 0.9), (0.92, 0.2, 0.09, 0.85), (1.75, 0.72, 0.1, 0.9)]
    small = []
    for _ in range(170):
        k = rnd.random() ** 1.6                       # most of them far off
        small.append((rnd.uniform(-7.4, 1.95), rnd.uniform(-0.6, 0.97), 0.014 + 0.05 * k, k * 0.75))
    small = [b for b in small if all(math.hypot(b[0] - c[0], b[1] - c[1]) > c[2] + b[2] for c in big)]
    bokeh = [(rnd.uniform(-7.4, 1.95), rnd.uniform(-0.6, 1.0), rnd.uniform(0.04, 0.11), rnd.choice("a5 a7 a8 a3".split()))
             for _ in range(70)]
    near_small = _buckets(small)
    rows_now = [28]                                   # set by texts(): the size being drawn
    near_bokeh = _buckets(bokeh, 0.25)
    # the film's colours as it thins: no g and no w (the theme's olive) anywhere
    film = pal.path("t2 a1 a0 a5 a6 a9 t5 a7 a2 t1 t2")
    swirl = pal.path("a2 a5 a8 a6 t3 a1 a2")
    glow_x, glow_y = 1.35, 0.5                       # where the light behind comes from

    def backdrop(x, y):
        """The rosy room: darker above, a warm pool of light low right,
        soft haze and blurred discs of light."""
        haze = fbm(x * 1.6, y * 2.4, 5)
        pool = math.exp(-((x - glow_x) / 0.75) ** 2 - ((y - glow_y) / 0.5) ** 2)
        t = clamp(0.1 + clamp(y + 0.2) * 0.1 + pool * 0.62 + (haze - 0.5) * 0.2)
        c = pal.path("- - a0 a1 a2 a3 a5 a7")(t)
        for bx, by, r, hue in near_bokeh(x, y):
            d = math.hypot(x - bx, y - by) / r
            if d < 1:
                c = mix(c, pal.rgb(hue), 0.3 * clamp((1 - d) * 1.6) * (0.5 + 0.5 * (r > 0.08)))
        return c

    def skin(x, y, bx, by, r, k):
        """A bubble's colour at (x, y): k is how near it is (sharpness)."""
        u, v = (x - bx) / r, (y - by) / r
        d = math.hypot(u, v)
        # the room behind, flipped and shrunk by the bubble, a little darker
        seen = mix(backdrop(bx - u * r * 0.75, by - v * r * 0.75), pal.ground, 0.3)
        # thin-film colour: bands swirling with the film's thickness, which
        # drains thinner at the top
        ang = math.atan2(v, u)
        flow = fbm(u * 1.4 + bx * 3, v * 1.4 + by * 3, 8)
        phase = ang / 6.283 + flow * 0.6 - v * 0.2 + bx
        hue = film(phase % 1.0)
        fresnel = clamp((d - 0.3) / 0.6) ** 1.4
        c = mix(seen, hue, (0.15 + 0.85 * fresnel) * (0.55 + 0.45 * k))
        # swirling bands of colour drifting over the face
        vein = clamp(1 - abs(fbm(u * 1.1 + bx * 7, v * 1.6 + by * 7, 9) - 0.5) * 9)
        c = mix(c, swirl((phase + 0.3) % 1.0), vein * 0.5 * k * (1 - fresnel))
        if d > 0.9:                                    # the bright rim
            c = mix(hue, pal.rgb("t6"), 0.1 + 0.25 * k)
        elif d > 0.82:                                 # a darker line just inside it
            c = mix(c, pal.rgb("x0"), 0.35 * k)
        # the soft second reflection: a crescent low right
        cres = clamp(1 - abs(ang - 0.75) / 0.7) * clamp(1 - abs(d - 0.7) / 0.14)
        c = mix(c, pal.rgb("t5"), cres * 0.55 * k)
        # the window glint, top left: a hard bright pane and a small dot
        gu, gv = u + 0.4, v + 0.4
        if (gu - gv) ** 2 / 0.12 + (gu + gv) ** 2 / 0.025 <= 1:          # along the curve
            return mix(c, pal.rgb("t9"), 0.4 + 0.6 * k)
        if math.hypot(u + 0.02, v + 0.66) < 0.08:
            return mix(c, pal.rgb("t8"), 0.8 * k)
        # far bubbles melt into the haze
        return mix(backdrop(x, y), c, 0.45 + 0.55 * k)

    def field(x, y):
        for bx, by, r, k in big:
            if (x - bx) ** 2 + (y - by) ** 2 <= r * r:
                return skin(x, y, bx, by, r, k), 1.0, True, "bubble"
        hit = None
        for b in near_small(x, y):
            if b[2] * rows_now[0] < 0.5:                 # under half a row: a speck, not a bubble
                continue
            if (x - b[0]) ** 2 + (y - b[1]) ** 2 <= b[2] * b[2] and (hit is None or b[3] > hit[3]):
                hit = b
        if hit:
            return skin(x, y, *hit), 1.0, False, "bubble"
        return backdrop(x, y), 1.0, False, "haze"

    def texts(rows, x_left, cw, unit):
        # the farthest bubbles, too small to draw, and a few sparkles
        rows_now[0] = rows
        rng = random.Random(31)
        out = []
        for _ in range(rows * 5):
            x, y = rng.uniform(-3.2, 1.9), rng.uniform(0.0, 1.0)
            if field(x, y)[3] != "haze":
                continue
            out.append((_col(x, x_left, cw), int(y / unit), rng.choice("°°·.'"),
                        rng.choice([pal.rgb("a5"), pal.rgb("a7"), pal.rgb("t4"), pal.rgb("a3")]), False))
        return out

    return scene("bubbly", field, texts, inks={"haze": "a", "bubble": "at"})


# ---------------------------------------------------------------- aurora

def _snowy_pine(cx, base, height, width, tiers=6):
    """A pine with snow along the bottom of each tier: where(x, y) -> None
    outside, else "snow", "rim" (its right edge, lit from the sky) or
    "needles"."""
    def where(x, y):
        t = (base - y) / height
        if t < 0 or t > 1:
            return None
        dx = x - cx
        if t < 0.07:
            return "needles" if abs(dx) < width * 0.09 else None
        k = (t - 0.07) / 0.93
        tier = (k * tiers) % 1.0
        half = width * (1 - k) * (0.5 + 0.5 * (1 - tier) ** 1.4) + width * 0.02
        if abs(dx) > half:
            return None
        if tier < 0.2 + 0.1 * math.sin(x * 300) and abs(dx) > half * 0.25:
            return "snow"
        if dx > half - width * 0.12:
            return "rim"
        return "needles"
    return where


def _curtain(base, waves, height, strength, seed):
    """One aurora ribbon: its lower edge base + sum of sine waves; at(x, y)
    -> (glow 0..1, how far up into the ribbon 0..1) or None."""
    def edge(x):
        return base + sum(a * math.sin(x * k + p) for a, k, p in waves)

    def at(x, y):
        b = edge(x)
        d = b - y
        if d < -0.02 or d > height * 2.5:
            return None
        if d < 0:
            return -d / 0.02, -1.0                         # the pink fringe under the edge
        slope = abs(edge(x + 0.004) - edge(x - 0.004)) / 0.008
        fold = 0.65 + min(0.6, slope * 0.9)               # folds catch more light
        rays = 0.55 + 0.3 * noise(x * 22, y * 1.5 + x, seed) + 0.15 * noise(x * 45, y * 2, seed + 1)
        glow = math.exp(-d / height) * fold * rays * strength * 1.5
        if d < 0.012:
            glow = max(glow, strength * (1 - d / 0.03))   # the bright lower edge
        h = d / (height * 2.5)
        glow = max(glow, 0.45 * strength * rays * math.exp(-((h - 0.6) / 0.22) ** 2))   # a rose haze on top
        return clamp(glow), h
    return at


def aurora(pal):
    """Northern lights over a frozen lake: folded curtains, bright and
    green along their lower edges, fading up through teal to rose; a snowy
    log cabin with lit windows among snow-laden pines, everything mirrored
    in the still water."""
    shore = 0.76
    curtains = [
        _curtain(0.22, ((0.06, 2.1, 0.4), (0.03, 5.3, 2.0)), 0.1, 0.6, 5),
        _curtain(0.38, ((0.1, 1.6, 2.2), (0.035, 4.1, 0.3), (0.012, 11, 1.0)), 0.16, 1.0, 9),
        _curtain(0.52, ((0.07, 2.7, 4.0), (0.03, 6.2, 1.1)), 0.1, 0.8, 13),
    ]
    up = pal.path("t8 a9 a7 a6 a4 x4 e5 e4")
    hills = ridge([(-0.6, 0.5, 0.08), (0.2, 0.45, 0.11), (0.85, 0.3, 0.06), (1.5, 0.5, 0.1), (2.1, 0.4, 0.12)],
                  shore)
    trees = [_snowy_pine(x, b, h, w) for x, b, h, w in
             ((1.13, 0.775, 0.24, 0.07), (1.58, 0.78, 0.34, 0.09), (1.73, 0.79, 0.42, 0.11),
              (1.86, 0.785, 0.3, 0.08), (1.04, 0.77, 0.15, 0.05))]
    far = [pine(x, shore, h, w, 5) for x, h, w in ((-0.3, 0.06, 0.025), (-0.24, 0.08, 0.03), (0.42, 0.05, 0.02),
                                                    (0.47, 0.07, 0.025), (0.53, 0.05, 0.02))]
    cab = (1.24, 1.47, shore - 0.075, shore + 0.005)      # x0, x1, wall top, base

    def bank(x):
        """The snowy bank the cabin stands on (right of the lake)."""
        return shore + 0.03 - 0.045 * clamp((x - 0.98) / 0.14) + 0.004 * math.sin(x * 37)

    def sky(x, y):
        c = pal.path("- - - d0 d1")(clamp(y / shore))
        c = mix(c, pal.path("a2 x2")(0.5 + 0.5 * math.sin(x * 1.3)), math.exp(-((shore - y) / 0.16) ** 2) * 0.6)  # airglow
        for at in curtains:
            hit = at(x, y)
            if hit is None:
                continue
            glow, h = hit
            if h < 0:
                c = mix(c, pal.rgb("e4"), 0.3 * (1 - glow))
            else:
                c = mix(c, up(clamp(h * 1.3)), glow)
        return c

    def cabin(x, y):
        x0, x1, top, base = cab
        mid = (x0 + x1) / 2
        roof = top - 0.07 * (1 - abs(x - mid) / ((x1 - x0) / 2 + 0.03))
        if 1.41 < x < 1.44 and top - 0.09 < y < top - 0.02:
            return pal.rgb("x2") if y > top - 0.083 else pal.rgb("t6")      # the chimney, snow on top
        if x0 - 0.03 < x < x1 + 0.03 and roof - 0.012 < y < top + 0.004:
            return pal.path("t9 t7 t5")(clamp((y - roof + 0.012) / 0.035))  # snow on the roof
        if x0 < x < x1 and top <= y <= base:
            for wx in (1.29, 1.39):
                if wx < x < wx + 0.04 and top + 0.02 < y < top + 0.05:
                    if abs(x - wx - 0.02) < 0.003 or abs(y - top - 0.035) < 0.003:
                        return pal.rgb("x1")
                    return pal.path("w9 w7")(clamp((y - top - 0.02) / 0.03))
            if 1.345 < x < 1.375 and y > top + 0.025:
                return pal.rgb("x1")                                        # the door
            log = int((y - top) / 0.0125) % 2
            return pal.path("x5 x3 x2")(clamp((x - x0) / (x1 - x0)) * 0.6 + log * 0.3)
        return None

    def field(x, y):
        c = cabin(x, y)
        if c is not None:
            return c, 1.0, True, "cabin"
        for tr in trees:
            part = tr(x, y)
            if part:
                c = {"snow": pal.rgb("t7"), "rim": pal.rgb("a3"), "needles": pal.path("- d0")(0.35)}[part]
                return c, 1.0, True, "tree"
        if x > 0.98 and y >= bank(x):
            depth = y - bank(x)
            if y < shore + 0.025 + 0.1 * clamp((x - 1.0) / 0.25) ** 0.7:
                light = sum(math.exp(-((x - wx - 0.02) / 0.05) ** 2) for wx in (1.29, 1.39)) * math.exp(-((y - shore) / 0.03) ** 2)
                c = pal.path("t6 t4 d4 d2")(clamp(depth / 0.09))
                c = mix(c, pal.rgb("w7"), clamp(light * 0.6))
                return c, 1.0, False, "snow"
        if any(t(x, y) for t in far):
            return pal.path("- d0")(0.5), 1.0, False, "sky"
        if y < shore:
            top = hills(x)
            if y >= top:
                k = (y - top) / 0.05
                c = pal.path("t4 d3 d0 -")(clamp(k * 0.8 + noise(x * 50, y * 50, 3) * 0.5))
                return mix(c, pal.rgb("a4"), 0.35 * clamp(1 - k)), 1.0, False, "hill"
            return sky(x, y), 1.0, False, "sky"
        # the lake: the sky mirrored, broken by slow ripples
        t = (y - shore) / (1 - shore)
        wob = 0.008 * math.sin(y * 230 + math.sin(x * 9) * 2)
        my = shore - (y - shore) * 1.25
        if my >= hills(x + wob):
            c = pal.path("d0 -")(clamp((shore - my) / 0.06))
        else:
            c = sky(x + wob, max(0.0, my))
        c = mix(c, pal.ground, 0.15 + t * 0.3)
        if math.sin(y * 420 + math.sin(x * 6) * 3) > 0.9:
            c = mix(c, pal.rgb("d3"), 0.35)
        for wx in (1.31, 1.41):                                # the windows' light on the water
            if abs(x - wx) < 0.012 + t * 0.01 and math.sin(y * 300) > -0.2:
                c = mix(c, pal.rgb("w6"), 0.7 * (1 - t))
        return c, 1.0, False, "lake"

    def lines(rows):
        return [([(1.425 + 0.012 * math.sin(k * 0.8) + k * 0.006, cab[2] - 0.1 - k * 0.025) for k in range(8)],
                 pal.rgb("d6"), False, None)]

    def texts(rows, x_left, cw, unit):
        out = stars(field, rows, x_left, cw, unit, rows * 9, 0.6, [pal.rgb("t9"), pal.rgb("t6"), pal.rgb("d8")], 17)
        return out + stars(field, rows, x_left, cw, unit, rows // 3, 0.4, [pal.rgb("t9"), pal.rgb("w8")], 23,
                           chars="+*")

    return scene("aurora", field, texts, lines,
                 inks={"sky": "dagxe", "hill": "dta", "lake": "dagxew", "snow": "tdw", "cabin": "xwtd",
                       "tree": "dta"})


# ---------------------------------------------------------------- synthwave

def _floor_rows(rows, hz, first=1.0, step=0.25):
    """The neon floor's cross lines for a picture `rows` tall: evenly
    spaced in depth, so bunching towards the horizon. Returns (near, far):
    near lines snapped to cell edges (row numbers, drawn as eighth-block
    lines) while they're a row or more apart, then far ones as y in braille
    dot rows, every one that's clear of the last (four dots near the
    viewer, two at the horizon), right up to the horizon (denser and
    denser, so the grid runs into the glow)."""
    near, far, n = [], [], 0
    last, last_dot = None, None
    horizon = math.floor(hz * rows * 4) + 1             # the first dot row below it
    while n < 5000:
        t = 1 / (first + n * step)
        y = hz + (1 - hz) * t
        nxt = hz + (1 - hz) / (first + (n + 1) * step)
        n += 1
        if not far and (y - nxt) * rows >= 1.0:
            b = round(y * rows)
            if b != last and b * 1.0 / rows > hz + 0.5 / rows:
                near.append(b)
                last = b
            continue
        r = math.floor(y * rows * 4)
        if r <= horizon:
            break
        top = ((last if last is not None else rows) - 1) * 4    # not in the last near line's cell
        need = 2 + round(2 * clamp(t * 2.5 - 0.25))       # sparser nearer the viewer
        if r < top and (last_dot is None or r <= last_dot - need):
            far.append((r + 0.5) / (rows * 4))
            last_dot = r
    return near, far


def _long_lines(rows, hz, sx, spread, lo=-46, hi=4):
    """The floor's long lines for a picture `rows` tall: (x at the bottom,
    t where it starts) for each, all meeting at (sx, hz). Evenly spaced
    along the bottom near the middle; further out, where they lie flatter,
    only every so many, so each stays clear of the next; each starts where
    it's a cell (two dots across) clear of its neighbours (no moire at
    the horizon)."""
    depth = 1 - hz
    cands = sorted((sx + k * spread for k in range(lo, hi + 1) if abs(k) > 3),   # the road covers the rest
                   key=lambda xb: abs(xb - sx))
    ang = lambda xb: math.atan2(xb - sx, depth)
    kept = []
    for xb in cands:                                    # outwards from the middle
        side = [a for a in kept if (a - sx) * (xb - sx) > 0 or a == sx]
        near = min(side, key=lambda a: abs(a - xb)) if side else None
        reach = math.hypot(xb - sx, depth)
        if near is None or abs(ang(xb) - ang(near)) * reach >= 1.6 / rows:
            kept.append(xb)
    kept.sort()
    out = []
    for i, xb in enumerate(kept):
        gaps = [abs(ang(xb) - ang(o)) for o in kept[max(0, i - 1):i + 2] if o != xb]
        gap = min(gaps) if gaps else 1.0
        reach = math.hypot(xb - sx, depth)
        out.append((xb, clamp(0.8 / rows / max(gap * reach, 1e-6), 0.02, 0.95)))
    return out


def grid(pal):
    """Outrun: a striped neon sun over dark mountains, a clean neon grid
    racing to a glowing horizon - cross lines as crisp eighth-block lines
    snapped to the cells, the long lines in braille, all meeting under the
    sun - a road with neon edges, and a lone car seen from behind, its tail
    lights throwing a red glow on the road."""
    hz = 0.6
    sx, sy, sr = 1.25, 0.38, 0.24
    mounts = ridge([(0.4, 0.4, 0.14), (1.7, 0.35, 0.16), (-0.6, 0.5, 0.12), (-2.0, 0.6, 0.16),
                    (-3.4, 0.5, 0.12), (-4.8, 0.65, 0.17), (-6.3, 0.5, 0.13)], hz)
    spread = 0.2                                    # the long lines' spacing along the bottom
    cy, half = 0.86, 0.155                          # the car, as a share of the picture
    road = lambda x, t: abs(x - sx) < 0.035 + t * 0.6
    rows_now = [28]                                  # set by texts(): the size being drawn
    cache = {}

    def cross(rows):
        if rows not in cache:
            cache[rows] = _floor_rows(rows, hz)
        return cache[rows]

    def longs(rows):
        """The long lines across the whole floor: (x at the bottom, t
        where each starts)."""
        if ("long", rows) not in cache:
            cache[("long", rows)] = _long_lines(rows, hz, sx, spread)
        return cache[("long", rows)]

    def crossed(x, b, rows):
        """Whether a long line runs through the cell just above row edge
        b at x (that cell is braille, so the cross line goes through it in
        braille too)."""
        cw = 0.5 / rows
        x_left = 1.9 - max(round(1.9 / cw), art_combined.SPAN_COLS) * cw
        xa = x_left + math.floor((x - x_left) / cw) * cw
        t1, ta = (b / rows - hz) / (1 - hz), ((b - 1) / rows - hz) / (1 - hz)
        for side in (-1, 1):                                # the road's edges
            x0, x1 = sx + side * (0.035 + 0.6 * ta), sx + side * (0.035 + 0.6 * t1)
            if max(x0, x1) >= xa and min(x0, x1) < xa + cw:
                return True
        for xb, start in longs(rows):
            t0 = max(start, ta)
            if t1 < t0:
                continue
            x0, x1 = sx + (xb - sx) * t0, sx + (xb - sx) * t1
            if max(x0, x1) >= xa and min(x0, x1) < xa + cw:
                return True
        return False

    def car(x, y):
        """What part of the car is at (x, y), or None: "glass", "roof",
        "lip", "deck", "lamp", "slat", "grille", "plate", "pipe", "bumper",
        "tyre"."""
        u, v = (x - sx) / half, (y - cy) / 0.08          # v -1 roof .. 1 road
        if not (-1.0 <= u <= 1.0 and -1.05 <= v <= 1.0):
            return None
        if v > 0.6:
            return "tyre" if 0.62 < abs(u) < 0.94 else None
        if v < -0.45:                                       # the cabin, narrower
            w = 0.62 + (v + 1.05) * 0.35
            if abs(u) > w:
                return None
            return "roof" if v < -0.92 or abs(u) > w - 0.07 else "glass"
        if abs(u) > 0.97:
            return None
        if v < -0.36:
            return "lip"                                    # the spoiler's edge catches the sun
        if v < -0.2:
            return "deck"
        if v < 0.22:
            if abs(u) > 0.42:
                return "lamp"
            return "slat" if math.sin(v * 22) > 0.2 else "grille"
        if v < 0.48 and abs(u) < 0.2:
            return "plate"
        if 0.4 < v < 0.6 and 0.24 < abs(u) < 0.36:
            return "pipe"
        return "bumper"

    def field(x, y):
        if y < hz:
            d = math.hypot(x - sx, y - sy)
            top = mounts(x)
            haze = math.exp(-((hz - y) / 0.035))         # the glow along the horizon
            if y >= top:
                edge = y - top < 0.01
                c = pal.rgb("a6") if edge else pal.path("x1 d1 -")((y - top) * 4)
                return mix(c, pal.rgb("e5"), haze * 0.55), 1.0, False, "mountain"
            if d <= sr:
                t = (y - sy + sr) / (2 * sr)
                gap = t > 0.45 and math.sin(t * 60) > 1.6 - t * 1.8
                if not gap:
                    return pal.path("w8 w6 a8 a6 e6")(t), 1.0, True, "sun"
            c = pal.path("- d1 x1 a4 e4")(clamp(y / hz))
            c = mix(c, pal.rgb("a6"), math.exp(-((d - sr) / 0.08) ** 2) * 0.5 * (d > sr))
            return mix(c, pal.rgb("e6"), haze * 0.5), 1.0, False, "sky"
        t = (y - hz) / (1 - hz)
        if 0.76 < y:
            part = car(x, y)
            if part:
                u = (x - sx) / half
                if part == "lamp":                      # two red light clusters, lit inside
                    return pal.path("e9 e7 e6")(clamp(abs(abs(u) - 0.7) * 4)), 1.0, True, "car"
                if part == "glass":                     # the rear window shows the sunset
                    return pal.path("a5 x3 d1 -")(clamp((y - (cy - 0.08)) / 0.055 + u * 0.3)), 1.0, True, "car"
                c = {"roof": "d2", "deck": "x2", "lip": "a6", "grille": "-", "slat": "e4", "plate": "t6",
                     "pipe": "e8", "bumper": "d1", "tyre": "-"}.get(part, "d1")
                return pal.rgb(c), 1.0, True, "car"
        rows = rows_now[0]
        near, _ = cross(rows)
        base = pal.path("x1 d0 -")(clamp(t * 3))
        glow = math.exp(-t / 0.035)                       # the horizon's glow on the floor
        base = mix(base, pal.rgb("e5"), glow * 0.55)
        on_road = road(x, t)
        if on_road:
            base = pal.path("x1 d0 -")(clamp(t * 1.6)) if t > 0.03 else base
            z = 1 / max(t, 1e-3)
            if abs(x - sx) < 0.004 + t * 0.012 and (z * 0.7) % 1.0 < 0.45:
                base = pal.path("w4 w6")(t)                 # the centre line
            # the car's tail lights on the road behind it
            red = math.exp(-((x - sx) / 0.22) ** 2 - ((y - 0.965) / 0.045) ** 2)
            base = mix(base, pal.rgb("e5"), red * 0.7)
            if ((x - sx) / (half * 1.05)) ** 2 + ((y - cy - 0.085) / 0.014) ** 2 <= 1:
                base = pal.ground                           # its shadow
        # a cross line: the last sample row or two above a cell edge
        row = y * rows
        b = math.ceil(row)
        if b in near and not on_road:
            tt = (b / rows - hz) / (1 - hz)
            thick = 2 if tt > 0.55 else 1
            if b - row <= thick / 8 and not crossed(x, b, rows):
                fade = clamp(1.2 - abs(x - sx) * 0.25)     # brightest under the sun
                return pal.path("a3 a5 a6 a7")(tt * (0.5 + 0.5 * fade)), 1.0, False, "grid"
        return base, 1.0, False, "grid"

    def neon(x, y):
        t = clamp((y - hz) / (1 - hz))
        return pal.path("a4 a6 a7")(t)

    def haze(x, y):
        return pal.path("e5 a3 a4 a6")(clamp((y - hz) / (1 - hz) / 0.35))

    def lines(rows):
        rows_now[0] = rows
        near, far = cross(rows)

        def off_floor(x, y):
            return road(x, (y - hz) / (1 - hz)) or (y > 0.76 and car(x, y) is not None)

        out = []
        # the long lines over the whole floor, each from where it's a cell
        # clear of its neighbours
        for xb, t0 in longs(rows):
            out.append(([(sx + (xb - sx) * t0, hz + (1 - hz) * t0), (xb, 1.0)], neon, False, off_floor))
        # the far cross lines, in braille, fading into the horizon's glow
        for y in far:
            out.append(([(-7.6, y), (2.2, y)], haze, False, off_floor))
        # the near cross lines through the cells a long line crosses
        for b in near:
            out.append(([(-7.6, (b - 0.3) / rows), (2.2, (b - 0.3) / rows)], neon, False,
                        lambda x, y, b=b: off_floor(x, y) or not crossed(x, b, rows)))
        # the road's neon edges
        for side in (-1, 1):
            out.append(([(sx + side * 0.035, hz), (sx + side * 0.635, 1.0)], pal.rgb("e7"), False,
                        lambda x, y: y > 0.76 and car(x, y) is not None))
        return out

    def texts(rows, x_left, cw, unit):
        rows_now[0] = rows
        return stars(field, rows, x_left, cw, unit, rows * 6, hz - 0.1, [pal.rgb("t9"), pal.rgb("a8")], 33)

    return scene("synthwave", field, texts, lines, inks={"grid": "axed", "car": "edatxw"})


# ---------------------------------------------------------------- deep sea

def jellyfish(pal):
    """Deep sea: a glowing jellyfish drifting up, its bell blushing from
    coral through violet to a cyan rim, lit from inside, a glowing frill,
    frilled pink arms and long tentacles in every colour; smaller jellies
    in their own hues, motes of plankton and light from far above."""
    jx, jy, jr = 1.3, 0.32, 0.16
    bell_light = sphere_light(jx, jy, jr, -0.2, -0.5)
    hues = ("e8", "a8", "w8", "x8", "g8", "e7", "a9")
    tentacles = [bezier((jx + dx, jy + 0.07), (jx + dx * 1.4 + 0.06 * math.sin(k * 1.7), 0.62),
                        (jx + dx * 1.1 - 0.12 + 0.03 * math.sin(k * 2.3), 0.99), 30)
                 for k, dx in enumerate((-0.13, -0.09, -0.05, -0.01, 0.03, 0.07, 0.11))]
    arms = strokes([(bezier((jx + dx, jy + 0.05), (jx + dx * 2 + 0.05, jy + 0.22), (jx + dx - 0.04, jy + 0.38), 14),
                     0.016, 0.004) for dx in (-0.035, 0.0, 0.035)])
    small = [(-0.4, 0.4, 0.05, "e"), (0.5, 0.65, 0.04, "w"), (0.15, 0.22, 0.048, "a"), (-1.8, 0.3, 0.05, "g"),
             (-2.6, 0.6, 0.035, "e")]

    def bell(x, y, cx, cy, r):
        u, v = (x - cx) / r, (y - cy) / (r * 0.75)
        return v <= 0.35 and u * u + v * v <= 1 and not (v > 0.2 and math.sin(u * 14) > 0.6)

    def main_bell(x, y):
        u, v = (x - jx) / jr, (y - jy) / (jr * 0.75)
        c = pal.path("e5 e6 e7 x8 a7 a6")(clamp((v + 1) / 1.25 + u * 0.12))
        r, ang = math.hypot(u, (v + 0.35) * 1.3), math.atan2(v + 0.35, u)
        if 0.15 < r < 0.5 and math.cos(ang * 4 + 0.8) > 0.1:
            c = pal.path("w9 w7")(r * 2)                            # the glowing gonads, four lobes
        elif math.sin(ang * 16) > 0.85 and r > 0.5 and v < 0.1:
            c = mix(c, pal.rgb("x8"), 0.6)                         # radial canals
        if v > 0.12:
            c = mix(c, pal.path("a9 t9")(clamp((v - 0.12) / 0.2)), 0.85)  # the frill
        light = bell_light(x, y)
        return mix(c, pal.rgb("t9"), clamp(light - 0.9) * 6)

    def field(x, y):
        if bell(x, y, jx, jy, jr):
            return main_bell(x, y), 1.0, True, "jelly"
        k = arms(x, y)
        if k is not None:
            frill = math.sin(y * 260 + x * 40) > 0.3
            return pal.path("e8 e6 x6 x4")(clamp(k + (0.15 if frill else 0))), 1.0, True, "jelly"
        for cx, cy, r, hue in small:
            if bell(x, y, cx, cy, r):
                v = (y - cy) / (r * 0.75)
                return pal.path(f"t9 {hue}9 {hue}7 {hue}6")(clamp((v + 0.9) / 1.3)), 1.0, False, "jelly2"
        glow = math.exp(-((x - jx) / 0.4) ** 2 - ((y - jy) / 0.35) ** 2)
        shaft = clamp(math.sin((x + y * 0.3) * 5) * 0.5 + 0.5) ** 10 * clamp(0.8 - y)
        c = pal.path("a4 d4 d1 -")(clamp(y * 1.2 + 0.1))
        c = mix(c, pal.rgb("x4"), glow * 0.35)
        c = mix(c, pal.rgb("e4"), math.exp(-((x - jx) / 0.24) ** 2 - ((y - jy + 0.03) / 0.18) ** 2) * 0.4)
        for cx, cy, r, hue in small:                                # each small jelly's own halo
            c = mix(c, pal.rgb(hue + "4"), math.exp(-((x - cx) / (r * 2)) ** 2 - ((y - cy) / (r * 1.6)) ** 2) * 0.4)
        return mix(c, pal.rgb("t6"), shaft * 0.3), 1.0, False, "water"

    def lines(rows):
        out = [(pts, pal.rgb(hues[k]), True, None) for k, pts in enumerate(tentacles)]
        for cx, cy, r, hue in small:
            out += [(bezier((cx + d, cy + 0.02), (cx + d * 1.6, cy + 0.12), (cx + d, cy + 0.25), 12),
                     pal.rgb(hue + "8"), False, None) for d in (-0.02, 0.0, 0.02)]
        return out

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(37)
        out = []
        for _ in range(rows * 4):
            x, y = rnd.uniform(-3.1, 1.9), rnd.uniform(0, 1)
            if field(x, y)[3] == "water":
                out.append((_col(x, x_left, cw), int(y / unit), rnd.choice(".·'°"),
                            rnd.choice([pal.rgb("a8"), pal.rgb("g8"), pal.rgb("t8"), pal.rgb("e8"), pal.rgb("w8")]),
                            False))
        return out

    return scene("deep sea", field, texts, lines,
                 inks={"water": "adgtxew", "jelly": "dgatewx", "jelly2": "dgatewx"})


# ---------------------------------------------------------------- phosphor

def _cell_probe():
    """The cell height a field is being sampled at. The renderer samples a
    field cell by cell from the top, 8 samples down a cell, so a render's
    first sample sits at y = unit / 16; a jump back up by more than half the
    picture means the next size has started. Lets a field line shapes up
    with the cells (crisp scanlines, quadrant keycaps)."""
    state = {"last": None, "unit": 1 / 28}

    def seen(y):
        if state["last"] is None or y < state["last"] - 0.5:
            state["unit"] = max(1 / 40, min(1 / 10, y * 16))
        state["last"] = y
        return state["unit"]
    return seen


_PIX = {"M": "101111101101101", "I": "111010010010111", "N": "110101101101101", "T": "111010010010010",
        "Y": "101101010010010", "P": "110101110100100", "E": "111100110100111"}


def terminal(pal):
    """A green phosphor terminal: a chunky retro CRT on a dark desk, its
    curved glass glowing, a pixel banner and a shell session with a block
    cursor on crisp scanlines, a keyboard in front."""
    cx0, cy0, cx1, cy1 = 0.84, 0.07, 1.86, 0.76          # the case
    sx0, sy0, sx1, sy1 = 0.95, 0.13, 1.75, 0.6           # the glass
    desk = 0.8
    probe = _cell_probe()
    session = [("$ ", "minitype --zen"), ("", "  ready.  92 wpm  99%"), ("$ ", "ls ~/words"),
               ("", "  en.txt  de.txt  fr.txt"), ("$ ", "█")]

    def layout(unit):
        """Banner (x, y, pixel) and the session's first row, for this size."""
        top = math.ceil(sy0 / unit) + 1
        px = unit / 2
        if (sx1 - sx0) / px < 33 or (sy1 - sy0) / unit < 9:
            return None, top
        bx = 1.9 - (round((1.9 - (sx0 + sx1) / 2) / px) + 16) * px
        return (bx, top * unit, px), top + 4

    def rounded(x, y, x0, y0, x1, y1, r):
        qx, qy = max(x0 + r - x, 0, x - x1 + r), max(y0 + r - y, 0, y - y1 + r)
        return x0 <= x <= x1 and y0 <= y <= y1 and qx * qx + qy * qy <= r * r

    def glass(x, y):
        u, v = (x - (sx0 + sx1) / 2) / ((sx1 - sx0) / 2), (y - (sy0 + sy1) / 2) / ((sy1 - sy0) / 2)
        return abs(u) ** 6 + abs(v) ** 6, u, v

    def screen(x, y, unit, u, v):
        f = (y / unit) % 1.0
        c = pal.path("- d0 d1 d2 d3")(clamp(0.85 - (u * u + v * v) * 0.6))
        banner, top = layout(unit)
        if banner:
            bx, by, px = banner
            i, j = int((x - bx) / px), int((y - by) / (px))
            if 0 <= j < 5 and 0 <= i < 31 and i % 4 != 3:
                ch = "MINITYPE"[i // 4]
                if _PIX[ch][j * 3 + i % 4] == "1":
                    return pal.path("t9 t8 t6 t5")(j / 4)
            if 0 <= j < 6 and -1 <= i < 32:
                c = mix(c, pal.rgb("d2"), 0.6)            # the banner's glow
        r = int(y / unit) - top
        if 0 <= r < len(session):
            n = len("".join(session[r]))
            col0 = sx0 + 0.05
            if col0 - unit * 0.5 < x < col0 + n * unit / 2 + unit * 0.5:
                c = mix(c, pal.rgb("d2"), 0.5)            # phosphor bloom behind the text
        light = math.exp(-(((u + 0.55) / 0.35) ** 2) - ((v + 0.6) / 0.25) ** 2)
        c = mix(c, pal.rgb("d6"), light * 0.45)           # a reflection on the curved glass
        if f > 0.74:
            c = mix(c, pal.ground, 0.65)                   # the scanline gap
        return c

    def field(x, y):
        unit = probe(y)
        g, u, v = glass(x, y)
        if g <= 1:
            return screen(x, y, unit, u, v), 1.0, True, "screen"
        if g <= 1.16 ** 6:
            # the recess round the glass: dark, lit along its bottom lip
            k = (g ** (1 / 6) - 1) / 0.16
            lip = v > 0.6
            return pal.path("- d1 d3 d5" if lip else "- d1 d2 d3")(k), 1.0, True, "case"
        if rounded(x, y, cx0, cy0, cx1, cy1, 0.05):
            edge = min(x - cx0, cx1 - x, y - cy0, cy1 - y)
            c = pal.path("d6 d5 d4 d3")(clamp(0.6 * (y - cy0) / (cy1 - cy0) + 0.4 * (x - cx0) / (cx1 - cx0)))
            if edge < 0.012:
                lit = (y - cy0 < 0.012) or (x - cx0 < 0.012 and cy1 - y > 0.012)
                c = pal.rgb("d8") if lit else pal.rgb("d1")
            elif y > 0.66:
                if 1.66 < x < 1.68 and 0.68 < y < 0.70:
                    return pal.rgb("g7"), 1.0, True, "case"       # power light
                if 1.72 < x < 1.8 and 0.675 < y < 0.705:
                    return pal.path("d2 d3")(clamp((x - 1.72) / 0.08)), 1.0, True, "case"
                if 0.98 < x < 1.32 and 0.7 < y < 0.715 and (x * 120) % 1 < 0.6:
                    c = pal.rgb("d3")                     # vent slots
            return c, 1.0, True, "case"
        if 1.17 < x < 1.53 and cy1 <= y < desk + 0.01:
            w = (y - cy1) / (desk - cy1)
            if abs(x - 1.35) < 0.1 + w * 0.08:
                return pal.path("d4 d2 d1")(w), 1.0, True, "case"   # the neck and foot
        # the keyboard
        if desk + 0.02 < y < 0.955 and 0.9 - (y - desk) * 0.4 < x < 1.82 + (y - desk) * 0.4:
            px = unit / 4
            qy = (y - (desk + 0.02)) / (unit / 2)
            qrow, qx = int(qy), int((1.9 - x) / px)
            if qrow % 2 == 1 or qrow >= 8 or y < desk + 0.02 + unit * 0.25:
                return pal.path("d3 d2")(clamp(qy / 8)), 1.0, True, "keys"
            kr = qrow // 2
            if kr == 3:
                key = 22 < qx < 74 and (qx < 30 or qx > 32) and (qx < 64 or qx > 66)
            else:
                key = (qx + kr) % 4 != 0 and 6 < qx < 90 - kr
            return (pal.path("d9 d8 d7")(kr / 3) if key else pal.rgb("d3")), 1.0, True, "keys"
        if 0.64 < x < 0.76 and 0.7 < y < desk:
            if 0.66 < x < 0.74:                            # a mug, lit from the screen
                k = (x - 0.66) / 0.08
                rim = y < 0.708
                return (pal.rgb("d6") if rim else pal.path("d1 d2 d4 d6 d3")(k)), 1.0, False, "desk"
            if x < 0.66 and 0.715 < y < 0.775 and abs(math.hypot((x - 0.66) / 0.018, (y - 0.745) / 0.03) - 0.8) < 0.3:
                return pal.rgb("d2"), 1.0, False, "desk"
        for k, (fx, fw) in enumerate(((0.3, 0.2), (0.32, 0.19), (0.29, 0.2))):
            fy = desk - 0.022 * (k + 1)
            if fy < y <= fy + 0.022 and fx < x < fx + fw:     # a stack of floppies
                if y < fy + 0.005:
                    return pal.rgb("d4"), 1.0, False, "desk"
                if fx + 0.05 < x < fx + 0.11 and k == 2:
                    return pal.rgb("w4"), 1.0, False, "desk"
                return pal.path("d3 d2")(k / 2), 1.0, False, "desk"
        if y >= desk:
            t = (y - desk) / (1 - desk)
            c = pal.path("d2 d1 d0 -")(clamp(t * 1.2 + 0.1))
            spill = math.exp(-((x - 1.35) / 0.55) ** 2) * (1 - t) * 0.6
            c = mix(c, pal.rgb("d3"), spill)
            if y < desk + 0.006:
                c = pal.rgb("d4")
            return c, 1.0, False, "desk"
        bloom = math.exp(-((x - 1.35) / 0.75) ** 2 - ((y - 0.38) / 0.45) ** 2)
        return pal.path("- d0 d1")(bloom * 0.9), 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        out = []
        _, top = layout(unit)
        last = int(sy1 / unit) - 1
        c0 = _col(sx0 + 0.05, x_left, cw)
        cmax = _col(sx1 - 0.03, x_left, cw)
        for i, (prompt, rest) in enumerate(session):
            r = top + i
            if r > last:
                break
            if r == last and prompt == "":
                break
            for k, ch in enumerate(prompt + rest):
                if ch == " " or c0 + k > cmax:
                    continue
                colour = ("w8" if k < len(prompt) else "t9" if prompt else "t7")
                out.append((c0 + k, r, ch, pal.rgb(colour), True))
        out.append((_col(1.12, x_left, cw), int(0.69 / unit), "m", pal.rgb("d8"), True))
        out.append((_col(1.12, x_left, cw) + 1, int(0.69 / unit), "t", pal.rgb("d8"), True))
        return out

    def lines(rows):
        return [([(0.69 + d + 0.012 * math.sin(k * 0.9 + d * 40), 0.69 - k * 0.022) for k in range(9)],
                 pal.rgb("d5"), False, None) for d in (-0.005, 0.02)]

    return scene("phosphor", field, texts, lines, inks={"screen": "dtw", "case": "dg", "keys": "d", "room": "d",
                                                        "desk": "dw"})


# ---------------------------------------------------------------- vaporwave

def palm_scene(pal):
    """The vaporwave sunset from art_combined (the one people love), at the
    revamp sizes."""
    sc = art_combined.vaporwave(pal)
    sc.sizes, sc.shade_cost, sc.theme = SIZES, SHADE, "vaporwave"
    field, lines, texts = sc.field, sc.lines, sc.texts

    def calm(focus, y):
        return focus and 0.06 < y < 0.9          # sky top and floor are backdrop
    sc.field = lambda x, y: (lambda c: (c[0], c[1], calm(c[2], y), c[3]))(field(x, y))
    sc.lines = lambda rows: [(p, col, foc and all(calm(True, py) for _, py in p), h)
                             for p, col, foc, h in lines(rows)]
    sc.texts = lambda rows, x_left, cw, unit: [(c, r, ch, col, foc and calm(True, (r + 0.5) * unit))
                                               for c, r, ch, col, foc in texts(rows, x_left, cw, unit)]
    return sc


# ---------------------------------------------------------------- summit

def summit(pal):
    """Above the clouds: a sharp summit at sunrise with a flag on top, a
    sea of clouds below lit pink and gold, distant peaks poking through."""
    peak = poly([(0.85, 0.95), (1.18, 0.55), (1.3, 0.5), (1.38, 0.24), (1.44, 0.3), (1.55, 0.45),
                 (1.75, 0.62), (1.95, 0.95)])
    others = ridge([(0.2, 0.25, 0.12), (-0.9, 0.3, 0.16), (-2.1, 0.25, 0.1)], 0.66)
    sea_top = 0.66

    def field(x, y):
        if 1.375 < x < 1.385 and 0.13 < y < 0.24:
            return pal.rgb("d4"), 1.0, True, "flag"
        if 1.385 <= x < 1.45 and 0.13 < y < 0.17 + 0.01 * math.sin(x * 120):
            return pal.rgb("e6"), 1.0, True, "flag"
        if peak(x, y):
            lit = x < 1.38 + (y - 0.24) * 0.6
            snow = fbm(x * 18, y * 18, 2) > 0.45 - (0.4 - y) * 0.8
            if snow:
                c = pal.path("e6 a6 a9")(clamp(0.8 - (y - 0.24))) if lit else pal.path("d4 g4 g6")(0.5)
            else:
                c = pal.path("x1 x4")(0.5) if lit else pal.path("- d1")(0.6)
            return c, 1.0, True, "peak"
        cloud = fbm(x * 4, y * 9, 7, 4)
        if y > sea_top - 0.05 + (0.5 - cloud) * 0.1:
            depth = y - sea_top
            sunlit = math.exp(-((x - 0.3) / 1.2) ** 2)
            c = pal.path("d4 g6 e6 a6 a9")(clamp(0.9 - depth * 1.8 + cloud * 0.3 - (1 - sunlit) * 0.3))
            return c, 1.0, False, "clouds"
        if y >= others(x):
            return pal.path("e4 d4 d1")(clamp((y - others(x)) * 4)), 1.0, False, "peaks"
        sunrise = math.exp(-((x - 0.3) / 0.8) ** 2 - ((y - 0.62) / 0.25) ** 2)
        c = pal.path("d1 d4 e4 e6 a8")(clamp(y * 1.1 + sunrise * 0.4))
        return c, 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 3, 0.25, [pal.rgb("a9")], 51, chars="..·")

    return scene("summit", field, texts, inks={"sky": "deag", "clouds": "dgea"})


MORE = {"rain": rain, "monitor": monitor, "plane": plane, "bolt": bolt, "rainbow": rainbow,
        "party": party, "glitch": glitch, "bubbles": bubbles, "aurora": aurora, "grid": grid,
        "jellyfish": jellyfish, "terminal": terminal, "palm": palm_scene, "summit": summit}
