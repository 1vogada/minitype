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

    def field(x, y):
        if in_amber(x, y):
            u, v = (x - ax) / ar, (y - ay) / (ar * 1.32)
            r = math.hypot(u, v)
            # the stone is lit from behind: brightest in the middle
            core = clamp(1.0 - r * 0.8)
            cloudy = fbm(x * 9, y * 9, 2) * 0.3 + fbm(x * 24, y * 24, 5) * 0.12
            t = clamp(core * 0.95 + cloudy * 0.35 + 0.15)
            if rex(x, y):
                # the animal shows as a darker amber: lit through where the
                # resin is thin, deeper where the body is thick
                return pal.path("x1 x4 g4 w6")(clamp(0.05 + core * 0.55)), 1.0, True, "rex"
            # no g6 in the path: the mix either side of it comes out olive
            c = pal.path("x1 x4 w6 w8 w9")(clamp(t * 1.35))
            if r > 0.86:                                    # the polished edge
                return pal.path("w6 w8 w9")(clamp(1 - (r - 0.86) * 3)), 1.0, True, "amber"
            return c, 1.0, True, "amber"
        # a warm halo on the table, then the dark room
        halo = math.exp(-(((x - ax) / 0.62) ** 2 + ((y - ay) / 0.55) ** 2))
        if y > 0.9:
            grain = fbm(x * 4, y * 40, 2)
            return mix(pal.path("- x1 a4 x4")(clamp(grain * 0.6)), pal.rgb("a4"), halo * 0.5), \
                1.0, False, "table"
        return pal.path("- x1 a4")(clamp(halo * 0.75)), 1.0, False, "room"

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

    return scene("amber", field, texts, inks={"amber": "xaw", "rex": "xa", "room": "xa", "table": "xa"})


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

def rainbow(pal):
    """A rainbow arcing over green hills after rain, clouds parting, the
    sun bursting through."""
    cx, cy = 1.25, 0.95
    bands = ["e6", "w6", "w8", "g6", "a6", "a4"]
    hills = [ridge([(0.3, 0.9, 0.1), (1.4, 0.8, 0.12), (-1.2, 1.0, 0.1)], 0.85),
             ridge([(0.9, 0.7, 0.08), (-0.4, 0.9, 0.07), (1.8, 0.4, 0.06)], 0.92)]
    clouds = soft_clouds([(0.4, 0.2, 0.5, 0.07), (1.7, 0.15, 0.35, 0.06), (-1.0, 0.25, 0.6, 0.07),
                          (-2.3, 0.18, 0.5, 0.06)])

    def field(x, y):
        if y >= hills[1](x):
            return pal.path("g6 g4 g1")(clamp((y - hills[1](x)) * 6)), 1.0, False, "hills"
        if y >= hills[0](x):
            return pal.path("g4 g1 d1")(clamp((y - hills[0](x)) * 5)), 1.0, False, "hills"
        r = math.hypot(x - cx, (y - cy) * 1.0)
        k = (0.62 - r) / 0.025
        if 0 <= k < len(bands):
            return pal.rgb(bands[int(k)]), 1.0, True, "rainbow"
        c = pal.path("d1 d4 t4 t6")(clamp(y * 1.1))
        cl = clouds(x, y)
        if cl:
            c = mix(c, pal.rgb("t8"), clamp(cl * 1.3))
        return c, 1.0, False, "sky"

    return scene("rainbow", field, None, None, inks={"sky": "dt", "hills": "gd"})


# ---------------------------------------------------------------- party

def party(pal):
    """Balloons floating up over a glowing floor, strings hanging, a few
    drifting away - party colours, a pinker room (no disco ball)."""
    # (x, y, radius); the strings of the lower ones reach the floor
    balloons = [(1.05, 0.26, 0.13), (1.42, 0.17, 0.1), (1.68, 0.35, 0.085),
                (0.78, 0.44, 0.075), (1.28, 0.52, 0.06)]

    def balloon(x, y):
        """(how far in 0..1, side -1..1) for the nearest balloon, or None."""
        best = None
        for bx, by, br in balloons:
            u, v = (x - bx) / br, (y - by) / (br * 1.22)
            d2 = u * u + v * v
            if d2 <= 1.0 and (best is None or d2 < best[0]):
                best = (d2, u, v)
        if best is None:
            return None
        d2, u, v = best
        return 1.0 - math.sqrt(d2), clamp(u)

    def field(x, y):
        b = balloon(x, y)
        if b:
            inside, side = b
            # a balloon is lit from the upper left, with a soft sheen line
            light = clamp(0.35 + inside * 0.75 - side * 0.22)
            # narrow stripes down the balloon, party colours
            s = int((side + 1.4) * 3.1) % 3
            tone = ("a4", "e6", "w8")[s]
            c = mix(pal.path("a1 a6 w8")(light), pal.rgb(tone), 0.35)
            glint = ((side + 0.5) * 2.2) ** 2 + ((inside - 0.62) * 3.4) ** 2 < 0.05
            if glint:
                c = pal.rgb("w9")
            elif inside < 0.06:
                c = mix(c, pal.rgb("w6"), 0.5)              # the rim catches light
            return c, 1.0, True, "balloon"
        for bx, by, br in balloons:
            # the knot, then the string, hanging from just under the balloon
            if abs(x - bx) < br * 0.12 and 0 < y - (by + br * 1.1) < br * 0.16:
                return pal.rgb("w8"), 1.0, True, "balloon"
            sway = 0.012 * math.sin((y - by) * 30 + bx * 4)
            if abs(x - bx - sway) < 0.004 and y > by + br * 1.16:
                return pal.rgb("t8"), 1.0, True, "balloon"
        if y > 0.8:
            t = (y - 0.8) / 0.2
            u = (x - 1.0) / (t + 0.3)
            tile = (math.floor(u * 4) + math.floor(t * 8)) % 2
            hue = ("a", "e", "w")[int(abs(math.floor(u * 4))) % 3]
            return pal.path("- " + hue + "4 " + hue + "6")(0.45 + tile * 0.5 * (1 - t * 0.5)), 1.0, False, "floor"
        # a warm pink glow rising off the floor, no beams
        glow = math.exp(-((y - 0.78) / 0.35) ** 2) * math.exp(-((x - 1.2) / 1.1) ** 2)
        c = pal.path("- d1")(0.3 - y * 0.2)
        return mix(c, pal.rgb("a4"), glow * 0.5), 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(19)
        out = []
        for _ in range(rows * 3):
            x, y = rnd.uniform(-3, 1.9), rnd.uniform(0.02, 0.78)
            if field(x, y)[3] == "room":
                out.append((_col(x, x_left, cw), int(y / unit), rnd.choice("*+.'~,"),
                            rnd.choice([pal.rgb("a8"), pal.rgb("e6"), pal.rgb("w8"), pal.rgb("t9")]),
                            False))
        return out

    return scene("party", field, texts, inks={"balloon": "aew", "room": "da", "floor": "aew"})


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
                    # no green on the skins (the owner asked for it out):
                    # pinks and warm whites only
                    return mix(bg, pal.path("a6 a8 w6 t8")(swirl), 0.85), 1.0, main, "bubble"
                return mix(bg, pal.path("a4 a6 t6")(swirl), 0.18 + (d ** 4) * 0.4), 1.0, main, "bubble"
        return field_bg(x, y)

    def field_bg(x, y):
        haze = fbm(x * 2, y * 3, 5)
        return pal.path("- d1 a1 a4")(clamp(0.2 + haze * 0.5 - y * 0.2)), 1.0, False, "haze"

    return scene("bubbly", field, inks={"haze": "da", "bubble": "atgd"})


# ---------------------------------------------------------------- aurora

def aurora(pal):
    """Northern lights rippling in curtains over a frozen lake, a cabin
    with a lit window among snowy pines, the curtains mirrored in ice."""
    shore = 0.78
    trees = [pine(x, shore + 0.01, h, w, 6) for x, h, w in ((1.55, 0.3, 0.09), (1.7, 0.4, 0.11), (1.83, 0.26, 0.08),
                                                         (1.18, 0.22, 0.07), (-0.6, 0.2, 0.06), (-1.9, 0.24, 0.07))]

    def curtain(x, y):
        best = 0.0
        for base, amp, ph, k in ((0.45, 0.12, 0.0, 2.3), (0.35, 0.1, 1.7, 1.6), (0.55, 0.08, 3.1, 3.0)):
            line = base + amp * math.sin(x * k + ph) + 0.03 * math.sin(x * 9 + ph)
            if y < line:
                fall = math.exp(-(line - y) / 0.18)
                rays = 0.6 + 0.4 * math.sin(x * 70 + ph * 5) ** 2
                best = max(best, fall * rays)
        return best

    def sky(x, y):
        c = pal.path("- d1 d4")(clamp(y * 0.8))
        a = curtain(x, y)
        c = mix(c, pal.path("a4 a6 a8 g6 e4")(clamp(1 - a + 0.0)), clamp(a * 1.4))
        return c

    def field(x, y):
        if any(t(x, y) for t in trees):
            snow = noise(x * 90, y * 60) > 0.6
            return (pal.rgb("t6") if snow else pal.ground), 1.0, x > 1.1, "tree"
        if 1.32 < x < 1.48 and shore - 0.08 < y < shore + 0.01:
            roof = y < shore - 0.055
            window = 1.37 < x < 1.41 and shore - 0.04 < y < shore - 0.015
            return (pal.rgb("t8") if roof else pal.rgb("w8") if window else pal.path("- x1")(0.6)), 1.0, True, "cabin"
        if y >= shore:
            my = shore - (y - shore) * 1.6
            c = sky(x, clamp(my, 0.0, shore))
            ice = pal.path("t4 d4 d1")(clamp((y - shore) * 3))
            return mix(c, ice, 0.55), 1.0, False, "lake"
        return sky(x, y), 1.0, False, "sky"

    def texts(rows, x_left, cw, unit):
        return stars(field, rows, x_left, cw, unit, rows * 7, 0.7, [pal.rgb("t9"), pal.rgb("t6")], 17)

    return scene("aurora", field, texts, inks={"sky": "dage", "lake": "dtag"})


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
    """Deep sea: a glowing jellyfish drifting up, its bell lit from inside,
    long trailing tentacles, motes of plankton and light from far above."""
    jx, jy, jr = 1.3, 0.32, 0.16
    bell_light = sphere_light(jx, jy, jr, -0.2, -0.5)
    tentacles = [bezier((jx + dx, jy + 0.06), (jx + dx * 1.5 + 0.08 * math.sin(k), 0.6), (jx + dx * 0.6 - 0.05 * k, 0.98), 30)
                 for k, dx in enumerate((-0.12, -0.07, -0.02, 0.03, 0.08, 0.12))]
    small = [(-0.4, 0.4, 0.05), (0.5, 0.65, 0.04), (-1.8, 0.3, 0.05), (-2.6, 0.6, 0.035)]

    def bell(x, y, cx, cy, r):
        u, v = (x - cx) / r, (y - cy) / (r * 0.75)
        return v <= 0.35 and u * u + v * v <= 1 and not (v > 0.2 and math.sin(u * 14) > 0.6)

    def field(x, y):
        if bell(x, y, jx, jy, jr):
            t = bell_light(x, y) * 0.6 + 0.4 * math.exp(-((y - jy - 0.02) / 0.06) ** 2)
            veins = math.sin(math.atan2(y - jy - 0.1, x - jx) * 14) > 0.85
            return pal.path("d4 g4 a6 t8 t9")(clamp(t + (0.15 if veins else 0))), 1.0, True, "jelly"
        for cx, cy, r in small:
            if bell(x, y, cx, cy, r):
                return pal.path("g4 a6")(0.6), 1.0, False, "jelly2"
        glow = math.exp(-((x - jx) / 0.4) ** 2 - ((y - jy) / 0.35) ** 2)
        shaft = clamp(math.sin((x + y * 0.3) * 5) * 0.5 + 0.5) ** 10 * clamp(0.8 - y)
        c = pal.path("a4 d4 d1 -")(clamp(y * 1.2 + 0.1))
        c = mix(c, pal.rgb("g6"), glow * 0.35)
        return mix(c, pal.rgb("t6"), shaft * 0.3), 1.0, False, "water"

    def lines(rows):
        out = [(pts, pal.rgb("a8"), True, None) for pts in tentacles]
        for cx, cy, r in small:
            out += [(bezier((cx + d, cy + 0.02), (cx + d * 1.6, cy + 0.12), (cx + d, cy + 0.25), 12),
                     pal.rgb("g6"), False, None) for d in (-0.02, 0.0, 0.02)]
        return out

    def texts(rows, x_left, cw, unit):
        rnd = random.Random(37)
        out = []
        for _ in range(rows * 4):
            x, y = rnd.uniform(-3.1, 1.9), rnd.uniform(0, 1)
            if field(x, y)[3] == "water":
                out.append((_col(x, x_left, cw), int(y / unit), rnd.choice(".·'°"),
                            rnd.choice([pal.rgb("a8"), pal.rgb("g8"), pal.rgb("t8")]), False))
        return out

    return scene("deep sea", field, texts, lines, inks={"water": "adgt", "jelly": "dgat"})


# ---------------------------------------------------------------- phosphor

def terminal(pal):
    """A green phosphor terminal: a big curved CRT glowing in the dark,
    a shell session on it with a block cursor, scanlines and bloom."""
    sx0, sy0, sx1, sy1 = 0.78, 0.1, 1.82, 0.78

    def field(x, y):
        u, v = (x - (sx0 + sx1) / 2) / ((sx1 - sx0) / 2), (y - (sy0 + sy1) / 2) / ((sy1 - sy0) / 2)
        if abs(u) ** 5 + abs(v) ** 5 <= 1:
            scan = math.sin(y * 380) > 0.4
            return pal.path("- d1 d4 a4")(clamp(0.62 - (u * u + v * v) * 0.3 - (0.1 if scan else 0))), 1.0, True, "screen"
        if abs(u) ** 5 + abs(v) ** 5 <= 1.35 ** 5:
            return pal.path("- d1")(0.35), 1.0, True, "bezel"
        if y > 0.86:
            return pal.path("d1 -")(clamp((y - 0.86) * 8)), 1.0, False, "desk"
        bloom = math.exp(-((x - 1.3) / 0.8) ** 2 - ((y - 0.45) / 0.5) ** 2)
        return pal.path("- d1")(bloom * 0.6), 1.0, False, "room"

    def texts(rows, x_left, cw, unit):
        out = []
        txt = ["$ ssh home", "welcome back.", "$ minitype --zen", "  ready.", "$ █"]
        r0 = int((sy0 + 0.08) / unit)
        step = max(1, int(0.075 / unit))
        for i, line in enumerate(txt):
            r = r0 + i * step
            if (r + 1) * unit > sy1 - 0.03:
                break
            for k, ch in enumerate(line):
                if ch != " ":
                    out.append((_col(sx0 + 0.1, x_left, cw) + k, r, ch, pal.rgb("t9" if ch == "$" else "t8"), True))
        return out

    return scene("phosphor", field, texts, inks={"screen": "dt", "bezel": "d", "room": "d"})


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
