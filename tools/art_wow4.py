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
    """An old amber CRT on a desk: a curved, glowing screen with text and
    scanlines, a chunky case, a keyboard in front, a warm halo."""
    sx0, sy0, sx1, sy1 = 0.92, 0.14, 1.62, 0.62

    def screen(x, y):
        u, v = (x - (sx0 + sx1) / 2) / ((sx1 - sx0) / 2), (y - (sy0 + sy1) / 2) / ((sy1 - sy0) / 2)
        return abs(u) ** 6 + abs(v) ** 6 <= 1, u, v

    def field(x, y):
        on, u, v = screen(x, y)
        if on:
            scan = math.sin(y * 360) > 0.3
            c = pal.path("- d1 x1 d4")(clamp(0.55 - (u * u + v * v) * 0.35 - (0.15 if scan else 0)))
            return c, 1.0, True, "screen"
        if sx0 - 0.07 <= x <= sx1 + 0.07 and sy0 - 0.06 <= y <= sy1 + 0.1:
            bevel = 0.6 if y < sy0 or x < sx0 else 0.35
            if sy1 + 0.04 < y and abs(x - (sx1 - 0.05)) < 0.015:
                return pal.rgb("a8"), 1.0, True, "case"            # the power light
            return pal.path("- d1 d4")(bevel), 1.0, True, "case"
        if 1.1 < x < 1.45 and sy1 + 0.1 < y < 0.8:
            return pal.path("- d1")(0.6), 1.0, True, "case"        # the stand
        kb = 0.84 < y < 0.93 and 0.8 + (0.93 - y) * 0.4 < x < 1.8 - (0.93 - y) * 0.4
        if kb:
            key = math.sin(x * 160) > -0.3 and math.sin(y * 260) > -0.4
            return pal.path("- d1 d4")(0.65 if key else 0.3), 1.0, True, "keyboard"
        if y > 0.8:
            return pal.path("d1 x1 -")(clamp((y - 0.8) * 5)), 1.0, False, "desk"
        halo = math.exp(-((x - 1.27) / 0.7) ** 2 - ((y - 0.38) / 0.45) ** 2)
        return pal.path("- x1 d1")(halo * 0.8), 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        out = []
        txt = ["> minitype", "", "wpm  112", "acc  98%", "", "> _"]
        r0 = int((sy0 + 0.08) / unit)
        step = max(1, int(0.07 / unit))
        for i, line in enumerate(txt):
            r = r0 + i * step
            if (r + 1) * unit > sy1 - 0.04:
                break
            for k, ch in enumerate(line):
                if ch != " ":
                    out.append((_col(sx0 + 0.08, x_left, cw) + k, r, ch, pal.rgb("t9" if k == 0 else "t8"), True))
        return out

    return scene("amber", field, texts, inks={"screen": "dxt", "case": "d", "room": "dx"})


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

def party(pal):
    """A mirror ball turning above a dance floor: faceted and glinting,
    beams of light fanning out, confetti, a glowing tiled floor."""
    bx, by, br = 1.3, 0.3, 0.16
    light = sphere_light(bx, by, br)

    def field(x, y):
        d = math.hypot(x - bx, y - by)
        if d <= br:
            u, v = (x - bx) / br, (y - by) / br
            lon = math.atan2(u, math.sqrt(max(0.0, 1 - u * u - v * v))) * 5
            lat = math.asin(clamp(v, -1, 1)) * 6
            tile = (math.floor(lon) + math.floor(lat)) % 3
            t = light(x, y) * 0.7 + tile * 0.15
            if noise(math.floor(lon) * 3.1, math.floor(lat) * 2.7) > 0.85:
                t = 1.0
            return pal.path("d1 d4 d6 t8 t9")(clamp(t)), 1.0, True, "ball"
        if abs(x - bx) < 0.006 and y < by - br:
            return pal.rgb("d4"), 1.0, True, "ball"
        if y > 0.8:
            t = (y - 0.8) / 0.2
            u = (x - 1.0) / (t + 0.3)
            tile = (math.floor(u * 4) + math.floor(t * 8)) % 2
            hue = ("a", "g", "e")[int(abs(math.floor(u * 4))) % 3]
            return pal.path("- " + hue + "4 " + hue + "6")(0.4 + tile * 0.5 * (1 - t * 0.5)), 1.0, False, "floor"
        ang = math.atan2(y - by, x - bx)
        beam = clamp(math.cos(ang * 9 + 0.5) * 0.5 + 0.5) ** 12 * math.exp(-max(0.0, d - br) * 1.2)
        hue = ("a6", "g6", "e6")[int((ang + 4) * 9 / math.pi) % 3]
        c = pal.path("- d1")(0.3 - y * 0.2)
        return mix(c, pal.rgb(hue), beam * 0.7), 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(19)
        out = []
        for _ in range(rows * 4):
            x, y = rnd.uniform(-3, 1.9), rnd.uniform(0.02, 0.8)
            if field(x, y)[3] == "room":
                out.append((_col(x, x_left, cw), int(y / unit), rnd.choice("*+.'~,"),
                            rnd.choice([pal.rgb("a8"), pal.rgb("g8"), pal.rgb("w8"), pal.rgb("t9"), pal.rgb("e6")]),
                            False))
        return out

    return scene("party", field, texts)


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

def bubbles(pal):
    """Big soap bubbles floating up through a soft pink haze: thin rims,
    swirls of colour on their skins, bright window glints."""
    rnd = random.Random(29)
    big = [(1.3, 0.45, 0.24), (1.72, 0.25, 0.12), (0.92, 0.2, 0.09), (1.75, 0.72, 0.1)]
    small = [(rnd.uniform(-3.1, 1.9), rnd.uniform(0.05, 0.95), rnd.uniform(0.015, 0.05)) for _ in range(60)]

    def field(x, y):
        for bx, by, r in big + small:
            d = math.hypot(x - bx, y - by) / r
            if d <= 1:
                main = (bx, by, r) in big
                rim = d > 0.86
                swirl = math.sin(math.atan2(y - by, x - bx) * 2 + d * 6 + bx * 5) * 0.5 + 0.5
                glint = math.hypot((x - bx) / r + 0.4, (y - by) / r + 0.45) < 0.16
                bg, _, _, _ = field_bg(x, y)
                if glint:
                    return pal.rgb("t9"), 1.0, main, "bubble"
                if rim:
                    return mix(bg, pal.path("a6 a8 g6 t8")(swirl), 0.85), 1.0, main, "bubble"
                return mix(bg, pal.path("a4 a6 t6")(swirl), 0.18 + (d ** 4) * 0.4), 1.0, main, "bubble"
        return field_bg(x, y)

    def field_bg(x, y):
        haze = fbm(x * 2, y * 3, 5)
        return pal.path("- d1 a1 a4")(clamp(0.2 + haze * 0.5 - y * 0.2)), 1.0, False, "haze"

    return scene("bubbly", field, inks={"haze": "da", "bubble": "atgd"})


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
        rays = 0.45 + 0.55 * noise(x * 55, y * 2 + x * 3, seed) ** 1.3
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

def grid(pal):
    """Outrun: a striped neon sun over wireframe mountains, a glowing grid
    racing to the horizon, a lone car's tail lights on the road."""
    hz = 0.6
    sx, sy, sr = 1.25, 0.38, 0.24
    mounts = ridge([(0.4, 0.4, 0.14), (1.7, 0.35, 0.16), (-0.6, 0.5, 0.12), (-2.0, 0.6, 0.16)], hz)

    def field(x, y):
        if y < hz:
            d = math.hypot(x - sx, y - sy)
            top = mounts(x)
            if y >= top:
                edge = y - top < 0.01
                return (pal.rgb("a6") if edge else pal.path("x1 d1 -")((y - top) * 4)), 1.0, False, "mountain"
            if d <= sr:
                t = (y - sy + sr) / (2 * sr)
                gap = t > 0.45 and math.sin(t * 60) > 1.6 - t * 1.8
                if not gap:
                    return pal.path("w8 w6 a8 a6 e6")(t), 1.0, True, "sun"
            c = pal.path("- d1 x1 a4 e4")(clamp(y / hz))
            return mix(c, pal.rgb("a6"), math.exp(-((d - sr) / 0.08) ** 2) * 0.5 * (d > sr)), 1.0, False, "sky"
        t = (y - hz) / (1 - hz)
        u = (x - sx) / (t + 0.04)
        line = abs(u - round(u * 2.5) / 2.5) < 0.012 / (t + 0.04) * 0.6 or abs(math.sin(1 / (t + 0.06) * 6)) < 0.12
        road = abs(x - sx) < 0.05 + t * 0.6
        c = pal.path("x1 d1 -")(t) if not road else pal.path("d1 -")(t * 0.7)
        if line and not road:
            c = pal.path("a8 a6 e6")(t)
        if road and abs(x - sx) < 0.004 + t * 0.01 and math.sin(1 / (t + 0.05) * 12) > 0:
            c = pal.rgb("w6")
        car = abs(x - sx - 0.04) < 0.09 and 0.8 < y < 0.86
        if car:
            light = 0.83 < y < 0.845 and abs(abs(x - sx - 0.04) - 0.065) < 0.02
            return (pal.rgb("e8") if light else pal.ground), 1.0, True, "car"
        return c, 1.0, False, "grid"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 6, hz - 0.1, [pal.rgb("t9"), pal.rgb("a8")], 33)

    return scene("synthwave", field, texts)


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
    small = [(-0.4, 0.4, 0.05, "e"), (0.5, 0.65, 0.04, "w"), (0.15, 0.2, 0.03, "a"), (-1.8, 0.3, 0.05, "g"),
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
