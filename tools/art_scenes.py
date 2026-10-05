"""The detailed corner pictures, as scenes for tools/artgen.py. Each is
named like the small pieces in minitype/terminal/art.py. See artgen.py for
the coordinates and the colour letters (d t e x a g w)."""

import math
import re

from artgen import (INF, Layer, Line, Mat, Scene, Shape, Stamp, below, bezier, circle,
                    ellipse, feather, grad, noise, poly, rect, ring, scatter, sphere, taper,
                    textured, union)

SCENES = {}
_MAKERS = {}


def scene(name):
    """Register a function that builds the named scene; they're all built
    at the end of the module, once every helper exists."""
    def add(fn):
        _MAKERS[name] = fn
        return fn
    return add


# ---------------------------------------------------------------- shared materials

def sea(top=0.8, part_lo="d", part_hi="a", amp=0.006, crest="t"):
    """Water from y=top down, any width: rows of ripples, denser further
    off, a lighter crest here and there."""
    surface = below(lambda x: top + amp * math.sin(x * 37) + amp * math.sin(x * 11 + 1))

    def tone(x, y):
        d = (y - top) / (1.0 - top + 1e-6)              # 0 at the horizon
        wave = math.sin(x * (70 - 40 * d) + y * 260 + 3 * math.sin(x * 7))
        return max(0.0, min(1.0, 0.45 + 0.5 * wave + 0.1 * (noise(x * 8, y * 30, 5) - 0.5)))
    return Layer(surface, Mat("  .-~~~", [(0, part_lo), (0.7, part_hi), (0.93, crest)],
                              edges=False), tone, focus=False)


def frond(base, tip, droop, width, mat, tone, focus=True):
    mid = ((base[0] + tip[0]) / 2, min(base[1], tip[1]) - droop)
    return Layer(taper(bezier(base, mid, tip), 0.004, 0.0, bulge=width), mat, tone, focus)


LEAF = Mat(" .:;*%#", [(0, "d"), (0.35, "g")], outline="g")
SAND = Mat(" .:;;+*", [(0, "d"), (0.35, "w")])
BARK = Mat("|):(I#", [(0, "d"), (0.4, "w")])


# ---------------------------------------------------------------- pictures

@scene("island")
def _():
    crown = (1.12, 0.3)
    leaf_t = grad(0.95, 0.15, 1.35, 0.5, 0.95, 0.35)
    fronds = []
    for tip, droop, w in [((0.97, 0.56), 0.02, 0.07), ((1.28, 0.53), 0.03, 0.07),
                          ((0.78, 0.46), 0.12, 0.09), ((1.50, 0.42), 0.12, 0.09),
                          ((0.86, 0.17), 0.07, 0.08), ((1.37, 0.12), 0.06, 0.08),
                          ((1.08, 0.04), 0.02, 0.07)]:
        fronds.append(frond(crown, tip, droop, w, LEAF, leaf_t))
        mid = ((crown[0] + tip[0]) / 2, min(crown[1], tip[1]) - droop)
        fronds.append(Line(bezier(crown, mid, tip, 12)[:-2], "t"))
    trunk = taper(bezier((1.22, 0.80), (1.26, 0.50), crown), 0.05, 0.03)
    sx, sy, sr = 0.42, 0.40, 0.15
    parts = [
        Layer(circle(sx, sy, sr), Mat(" .:-=+*#", [(0, "e"), (0.5, "w")], outline="e"),
              lambda x, y: 1 - math.hypot(x - sx, y - sy) / sr * 0.8),
        *[Line([(sx + math.cos(a) * sr * 1.25, sy + math.sin(a) * sr * 1.25),
                (sx + math.cos(a) * sr * 1.55, sy + math.sin(a) * sr * 1.55)], "w")
          for a in [math.pi * (1 + k / 6) for k in range(7)]],
        Stamp(0.05, 0.18, "v", "d"), Stamp(0.72, 0.10, "^v^", "d"),
        sea(),
        *[Stamp(sx - 0.07 + 0.012 * i, 0.83 + 0.035 * i, "=" * (9 - 2 * i), "w", False) for i in range(4)],
        Layer(ellipse(1.2, 0.83, 0.34, 0.07), SAND, grad(1.0, 0.76, 1.3, 0.85, 1, 0.2)),
        Layer(trunk, BARK, lambda x, y: 0.3 + 0.7 * (math.sin(y * 160) > 0)),
        *fronds,
        Layer(circle(1.10, 0.33, 0.022) | circle(1.15, 0.34, 0.02), Mat("oO@", [(0, "x")]), 0.6),
    ]
    return Scene(1.6, parts, span=True)


@scene("rose")
def _():
    cx, cy = 0.5, 0.3
    # petals from the outside in, each lit along its rim and darker where it
    # folds in, so every layer shows
    petals = [
        (ellipse(cx - 0.14, cy + 0.07, 0.15, 0.11, 25), (cx - 0.25, cy + 0.1)),
        (ellipse(cx + 0.15, cy + 0.07, 0.15, 0.11, -25), (cx + 0.26, cy + 0.1)),
        (ellipse(cx, cy + 0.11, 0.2, 0.1), (cx, cy + 0.2)),
        (ellipse(cx - 0.09, cy - 0.01, 0.13, 0.12, 15), (cx - 0.2, cy - 0.04)),
        (ellipse(cx + 0.1, cy - 0.02, 0.12, 0.12, -15), (cx + 0.2, cy - 0.05)),
        (ellipse(cx, cy - 0.06, 0.1, 0.085), (cx, cy - 0.14)),
    ]

    def rim(px, py):
        return lambda x, y: max(0.15, min(1.0, 1.05 - math.hypot(x - px, y - py) * 5.5))
    stem = bezier((cx - 0.01, cy + 0.2), (cx - 0.12, 0.65), (cx - 0.07, 0.98))
    leafmat = Mat(" .:;+*", [(0, "d"), (0.3, "g")], outline="g")
    leaf1 = taper(bezier((cx - 0.09, 0.72), (cx - 0.3, 0.6), (cx - 0.42, 0.66)), 0.01, 0, bulge=0.12)
    leaf2 = taper(bezier((cx - 0.08, 0.80), (cx + 0.12, 0.7), (cx + 0.30, 0.74)), 0.01, 0, bulge=0.13)
    spiral = [(cx + 0.006 * a * math.cos(a), cy - 0.06 + 0.005 * a * math.sin(a))
              for a in [k * 0.5 for k in range(4, 22)]]
    parts = [
        Layer(taper(stem, 0.025, 0.02), Mat("|", "g"), 0.7),
        Layer(leaf1, leafmat, grad(cx - 0.4, 0.66, cx - 0.1, 0.72, 0.4, 0.9)),
        Layer(leaf2, leafmat, grad(cx + 0.3, 0.74, cx - 0.1, 0.8, 0.4, 0.9)),
        Line(bezier((cx - 0.1, 0.72), (cx - 0.27, 0.64), (cx - 0.38, 0.66), 6), "g", tone=0.45),
        Line(bezier((cx - 0.08, 0.80), (cx + 0.1, 0.73), (cx + 0.26, 0.74), 6), "g", tone=0.45),
        Layer(ellipse(cx - 0.01, cy + 0.19, 0.09, 0.035), Mat(" .:+", "g", outline="g"), 0.6),
        *[Layer(shape, Mat(" .:-=+*#%", [(0, "d"), (0.25, "e"), (0.85, "t")], outline="e"), rim(px, py))
          for shape, (px, py) in petals],
        Line(spiral, "e", tone=0.25),
        Stamp(cx - 0.10, 0.88, ">", "g"), Stamp(cx - 0.115, 0.55, "<", "g"),
        grass(0.97),
        *[Stamp(1.0 - k * 0.11 - 0.05 * rand(k, 87), 0.95 + 0.03 * rand(k, 88), "o.,"[k % 3], "e",
                False, tone=0.4 + 0.4 * rand(k, 89)) for k in range(45)],
    ]
    return Scene(1.0, parts, span=True)


@scene("moon")
def _():
    cx, cy, R = 0.78, 0.36, 0.3
    disc = circle(cx, cy, R) - circle(cx + 0.16, cy - 0.09, R * 0.92)
    craters = [(cx - 0.16, cy - 0.05, 0.045), (cx - 0.09, cy + 0.16, 0.036),
               (cx - 0.2, cy + 0.11, 0.022), (cx - 0.04, cy + 0.24, 0.027)]

    def tone(x, y):
        t = sphere(cx, cy, R, -0.8, -0.2, 0.25, 1.0)(x, y)
        for kx, ky, kr in craters:
            d = math.hypot(x - kx, y - ky) / kr
            if d < 1:
                t -= 0.35 * (1 - d * 0.5)
        return max(0.0, t)
    parts = [
        *scatter(-3.0, 0.0, 1.4, 0.7, 70, ["*", ".", "+", ".", "'"], "t", seed=7),
        Layer(disc, Mat(" .:-=+*#%@", [(0, "d"), (0.35, "w")], outline="w"), tone),
        Stamp(0.15, 0.18, "*", "w"), Stamp(1.25, 0.12, "+", "w"),
        skyline(1.0, 3),
    ]
    return Scene(1.4, parts, span=True)


# ---------------------------------------------------------------- helpers for text scenes

def at(col, row, rows):
    """Scene coordinates of a character cell, for a scene `rows` tall."""
    return col / (2 * rows), (row + 0.5) / rows


def lines_at(col, row, rows, lines, parts):
    """Lines of text from a cell, coloured by `parts`: a letter, a string
    per line, or a {character: letter} map (others take its "" entry)."""
    out = []
    for k, line in enumerate(lines):
        if isinstance(parts, dict):
            p = "".join(parts.get(ch, parts[""]) for ch in line)
        elif isinstance(parts, (list, tuple)):
            p = parts[k]
        else:
            p = parts
        x, y = at(col, row + k, rows)
        out.append(Stamp(x, y, line, p))
    return out


def rand(i, seed=0):
    """A repeatable pseudo-random number in 0..1."""
    return noise(i * 1.618 + 0.37, seed * 2.71 + 0.5, seed) * 7.3 % 1.0




# ---------------------------------------------------------------- trees

def pine_tree(cx, base, top, width, tiers, mat, trunk=None, focus=True):
    """A conifer: `tiers` stacked, each with a drooping skirt and its own
    outline, lit from the left; the top tier is drawn last, over the rest."""
    h = base - top
    out = []
    if trunk:
        out.append(Layer(rect(cx - width * 0.05, top + h * 0.7, cx + width * 0.05, base),
                         trunk, 0.6, focus))
    lit = textured(lambda x, y: max(0.0, min(1.0, 0.8 - (x - cx) / width * 1.2)), 0.12, 40)
    for i in reversed(range(tiers)):
        t0 = top + h * 0.85 * i / tiers
        t1 = top + h * 0.85 * (i + 1.7) / tiers
        w = width * (0.3 + 0.7 * (i + 1) / tiers) / 2
        droop = (t1 - t0) * 0.22
        out.append(Layer(poly([(cx, t0), (cx + w, t1), (cx + w * 0.55, t1 - droop),
                               (cx, t1 - droop * 0.3), (cx - w * 0.55, t1 - droop),
                               (cx - w, t1)]), mat, lit, focus))
    return out


def treeline(base, height, spacing, seed=0, x_max=2.0):
    """The top of a far-off row of conifers, as a function of x: one
    jagged silhouette rather than many trees."""
    def top(x):
        best = base
        i0 = int((x_max - x) / spacing)
        for i in range(i0 - 2, i0 + 3):
            cx = x_max - i * spacing - rand(i, seed) * spacing * 0.5
            hgt = height * (0.6 + 0.4 * rand(i, seed + 1))
            y = base - hgt * max(0.0, 1 - abs(x - cx) / (hgt * 0.3))
            best = min(best, y)
        return best
    return top


NEEDLES = Mat(" .:;+*#%", [(0, "d"), (0.3, "g")], outline="g")
FAR_NEEDLES = Mat(" .:;", "d", outline="d")
TRUNK = Mat("|#", "w")


@scene("keyboard")
def _():
    layouts = {26: ["`1234567890-=", "QWERTYUIOP[]", "ASDFGHJKL;'", "ZXCVBNM,./"],
               20: ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
               14: ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"],
               10: ["ASDFGHJKL", "ZXCVBNM"]}
    indents = [0, 2, 3, 5]

    def width(rows):
        keys = layouts[rows]
        return max(indents[k] + 5 * len(r) + 1 for k, r in enumerate(keys)) + 2

    def keys(rows):
        out = desk(rows)
        layout = layouts[rows]
        height = 4 * len(layout) + (4 if rows == 26 else 0)
        row = rows - 2 - height
        frame = {"|": "d", "_": "d", "/": "d", "\\": "d", "": "a"}
        for k, keys_ in enumerate(layout):
            n = len(keys_)
            out += lines_at(indents[k], row, rows, [
                " " + "____ " * n,
                "".join(f"||{c} |" for c in keys_) + "|",
                "||__|" * n + "|",
                "|/__\\" * n + "|",
            ], frame)
            for st in out[-3:-2]:
                st.part = "".join("w" if ch in "FJ" else frame.get(ch, "a") for ch in st.text)
                st.tone = 0.8
            for st in out[-2:]:
                st.tone = 0.45
            row += 4
        if rows == 26:
            out += lines_at(16, row, rows, [
                " ____________________________ ",
                "||                          ||",
                "||__________________________||",
                "|/__________________________\\|"], frame)
        return out
    return Scene(lambda rows: width(rows) / (2 * rows), keys, span=True)


@scene("pines")
def _():
    parts = [
        Stamp(0.25, 0.12, "v", "d", False), Stamp(0.5, 0.06, "^v^", "d", False),
        Layer(below(lambda x: 0.55 + 0.08 * math.sin(x * 4.0) + 0.04 * math.sin(x * 9 + 1)),
              Mat(" .", "d", dither=True), 0.3, focus=False),
    ]
    parts.append(Layer(below(treeline(0.88, 0.3, 0.07, 3)), Mat(" .:", "d", dither=True),
                       0.55, focus=False))
    parts.append(Layer(below(lambda x: 0.9 + 0.02 * math.sin(x * 13)),
                       Mat(" .,;:", [(0, "d"), (0.5, "g")], edges=False),
                       textured(0.6, 0.35, 20), focus=False))
    for cx, top, w in [(0.75, 0.22, 0.38), (1.05, 0.02, 0.48), (1.32, 0.18, 0.36)]:
        parts += pine_tree(cx, 0.97, top, w, 6, NEEDLES, TRUNK)
    return Scene(1.6, parts, span=True)


@scene("sunset")
def _():
    hz = 0.6
    sx, sr = 1.0, 0.36
    sun = circle(sx, hz, sr) & rect(-INF, -INF, INF, hz)

    def sun_tone(x, y):
        k = (hz - y) / sr                       # 0 at the horizon, 1 at the top
        stripe = math.sin(k * 26) > 0.9 - k * 1.6
        return 0.0 if stripe and k < 0.6 else 0.35 + 0.65 * k
    parts = [
        *[Line([(sx + math.cos(a) * sr * 1.12, hz + math.sin(a) * sr * 1.12),
                (sx + math.cos(a) * sr * 1.42, hz + math.sin(a) * sr * 1.42)], "w")
          for a in [math.radians(190 + 20 * k) for k in range(9)]],
        Layer(sun, Mat(" -=+*#", [(0, "e"), (0.55, "x"), (0.8, "w")], edges=False), sun_tone),
        *[Layer(ellipse(x, y, rx, 0.018), Mat("-=", [(0, "d"), (0.5, "x")], edges=False),
                textured(0.5, 0.4, 30), focus=False)
          for x, y, rx in [(0.55, 0.22, 0.30), (1.25, 0.3, 0.25), (-0.4, 0.15, 0.5),
                           (-1.5, 0.28, 0.4), (-2.5, 0.2, 0.45), (0.9, 0.42, 0.18)]],
        Stamp(0.25, 0.25, "v", "d"), Stamp(0.4, 0.16, "^v^", "d"),
        sea(hz + 0.005, "d", "a", amp=0.002),
        *[Stamp(sx - sr * (0.75 - 0.12 * i), hz + 0.06 + 0.07 * i,
                "=" * max(2, int(sr * (1.5 - 0.25 * i) * 40)), "w" if i < 2 else "x", False)
          for i in range(5)],
    ]

    def with_boat(rows):
        if rows < 14:
            return parts
        row = int(hz * rows) - 5
        return parts + lines_at(int(0.3 * 2 * rows), row, rows, [
            "    |\\",
            "    | \\",
            "   /|  \\",
            "  / |___\\",
            " /__|",
            "\\_______/"], {"_": "d", "\\": "t", "/": "t", "|": "d", "": "t"})
    return Scene(1.45, with_boat, span=True)


@scene("stones")
def _():
    stones = [(0.85, 0.83, 0.26, 0.11), (0.83, 0.64, 0.2, 0.09), (0.87, 0.48, 0.15, 0.075),
              (0.84, 0.35, 0.10, 0.06), (0.855, 0.25, 0.06, 0.04)]
    parts = [Layer(below(lambda x: 0.9 + 0.015 * math.sin(x * 9)),
                   Mat(" .,:;", [(0, "d"), (0.45, "g")], edges=False),
                   textured(0.55, 0.4, 25), focus=False)]
    for i in range(60):
        x = 1.5 - i * 0.09 - rand(i, 5) * 0.05
        parts.append(Layer(ellipse(x, 0.93, 0.02 + 0.02 * rand(i, 6), 0.012),
                           Mat(" o", "d"), 0.8, focus=False))
    for k, (x, y, rx, ry) in enumerate(stones):
        parts.append(Layer(ellipse(x, y, rx, ry, -4 + 3 * k),
                           Mat(".:-=+*#%@", [(0, "d"), (0.45, "t")], outline="d"),
                           sphere(x, y, rx, -0.6, -0.8, 0.2, 1.0)))
        parts.append(Layer(ellipse(x - rx * 0.2, y - ry * 0.8, rx * 0.6, ry * 0.35),
                           Mat(",;:%", "g", edges=False), textured(0.6, 0.3, 40)))
    # a little mushroom and a fern
    parts += [
        Layer(ellipse(0.38, 0.86, 0.075, 0.05) & rect(0, 0, 9, 0.86),
              Mat(" .:+#", "e", outline="e"), sphere(0.38, 0.86, 0.075, -0.5, -0.8, 0.3, 1)),
        Layer(rect(0.365, 0.86, 0.395, 0.92), Mat("|", "t"), 0.8),
        Stamp(0.35, 0.83, "o", "t"), Stamp(0.40, 0.81, ".", "t"),
        *feather((1.25, 0.92), (1.45, 0.62), 0.05, 0.035, "g", every=0.035),
        *feather((1.2, 0.92), (1.12, 0.58), 0.04, 0.035, "g", every=0.035),
    ]
    return Scene(1.5, parts, span=True)


@scene("pine")
def _():
    parts = [
        *scatter(-3.0, 0.0, 1.0, 0.45, 50, ["*", ".", "+", "'"], "t", seed=11),
        Layer(circle(0.18, 0.18, 0.08) - circle(0.22, 0.15, 0.075),
              Mat(" .:+#", "w", outline="w"), 0.8),
        Layer(below(treeline(0.86, 0.24, 0.05, 9)), Mat(" .:", "d"), 0.5, focus=False),
        Layer(below(lambda x: 0.88 - 0.04 * math.cos((x - 0.55) * 3)),
              Mat(" .:-", [(0, "d"), (0.5, "t")], outline="t"), grad(0, 0.8, 1, 0.9, 0.9, 0.3),
              focus=False),
        *pine_tree(0.22, 0.88, 0.55, 0.22, 4, FAR_NEEDLES),
        *pine_tree(0.95, 0.9, 0.5, 0.25, 4, FAR_NEEDLES),
        *pine_tree(0.58, 0.95, 0.02, 0.62, 8, NEEDLES, TRUNK),
        Stamp(0.565, 0.025, "*", "w"),
    ]
    return Scene(1.1, parts, span=True)


@scene("leaf")
def _():
    right = [(0, -1.0), (0.13, -0.70), (0.32, -0.78), (0.26, -0.38), (0.52, -0.60), (0.58, -0.44),
             (0.88, -0.50), (0.76, -0.26), (0.98, -0.08), (0.56, 0.16), (0.64, 0.34), (0.22, 0.26),
             (0.06, 0.50)]
    shape = right + [(-x, y) for x, y in reversed(right)]
    cx, cy, s, a = 0.8, 0.42, 0.36, math.radians(12)

    def tf(x, y):
        return (cx + s * (x * math.cos(a) - y * math.sin(a)),
                cy + s * (x * math.sin(a) + y * math.cos(a)))
    base = tf(0, 0.42)
    tips = [tf(0, -1.0), tf(0.88, -0.5), tf(-0.88, -0.5), tf(0.98, -0.08), tf(-0.98, -0.08)]
    leaf_tone = textured(grad(cx, cy - s, cx, cy + s, 1.0, 0.1), 0.15, 20)
    parts = [
        Layer(below(lambda x: 0.93 + 0.015 * math.sin(x * 11)),
              Mat(" .,;", [(0, "d"), (0.5, "x")], edges=False), textured(0.5, 0.4, 25),
              focus=False),
    ]
    for i in range(70):
        x = 1.5 - i * 0.07 - rand(i, 9) * 0.05
        parts.append(Stamp(x, 0.9 + 0.06 * rand(i, 4), "*#&%"[i % 4], "ewx"[i % 3], False))
    parts += [
        Layer(poly([tf(x, y) for x, y in shape]),
              Mat(" .:;+*#%", [(0, "e"), (0.45, "x"), (0.75, "w")], outline="e"), leaf_tone),
        *[Line([base, (base[0] + (t[0] - base[0]) * 0.7, base[1] + (t[1] - base[1]) * 0.7)], "w")
          for t in tips[:3]],
        Line([base, tf(0, 0.95), tf(-0.05, 1.25)], "w"),
        Stamp(0.2, 0.25, "*", "x"), Stamp(0.35, 0.5, "&", "e"), Stamp(0.1, 0.65, "%", "w"),
        Stamp(1.45, 0.15, "*", "w"),
    ]
    return Scene(1.5, parts, span=True)


# ---------------------------------------------------------------- plants and places

def dunes(base, part_lo="d", part_hi="w", focus=False):
    """Rolling sand, any width, with ripples."""
    top = lambda x: base + 0.05 * math.sin(x * 3.1) + 0.025 * math.sin(x * 7.3 + 2)
    tone = lambda x, y: 0.45 + 0.35 * math.sin((y - top(x)) * 90 + x * 6) * (y > top(x) + 0.02) \
        + 0.25 * math.cos(x * 3.1)
    return Layer(below(top), Mat(" .-~=", [(0, part_lo), (0.55, part_hi)]), tone, focus)


@scene("cactus")
def _():
    def arm(x0, y0, side, up, out, w):
        x1 = x0 + side * out
        return union(taper([(x0, y0), (x1, y0)], w, w),
                     taper([(x1, y0), (x1, y0 - up)], w, w),
                     circle(x1, y0 - up, w / 2), circle(x1, y0, w / 2))
    cx = 1.05
    body = union(rect(cx - 0.055, 0.12, cx + 0.055, 0.9), circle(cx, 0.12, 0.055),
                 arm(cx, 0.55, -1, 0.22, 0.17, 0.085), arm(cx, 0.45, 1, 0.2, 0.16, 0.08))

    def ribs(x, y):
        lit = 0.75 - (x - cx) * 2.5
        return max(0.1, min(1.0, lit + 0.25 * math.cos(x * 160)))
    small = union(rect(0.6, 0.72, 0.64, 0.9), circle(0.62, 0.72, 0.02),
                  arm(0.62, 0.8, -1, 0.06, 0.05, 0.035))
    sun = circle(0.42, 0.3, 0.1)
    return Scene(1.4, [
        Layer(sun, Mat(" .:+*#", [(0, "x"), (0.5, "w")], outline="w"),
              lambda x, y: 1 - math.hypot(x - 0.42, y - 0.3) * 7),
        *[Line([(0.42 + math.cos(a) * 0.13, 0.3 + math.sin(a) * 0.13),
                (0.42 + math.cos(a) * 0.17, 0.3 + math.sin(a) * 0.17)], "w")
          for a in [k * math.pi / 4 for k in range(8)]],
        Stamp(0.15, 0.15, "v", "d"), Stamp(0.75, 0.1, "^v^", "d"),
        Layer(below(lambda x: 0.62 + 0.12 * max(0, 1 - abs(x + 0.3) * 2.5) + 0.04 * math.sin(x * 5)),
              Mat(" .:", "d"), 0.5, focus=False),
        dunes(0.86),
        Layer(body, Mat(" .:|!#", [(0, "d"), (0.35, "g")], outline="g"), ribs),
        Layer(small, Mat(" .:|!#", [(0, "d"), (0.35, "g")], outline="g"), ribs),
        Stamp(cx - 0.02, 0.085, "@", "e"), Stamp(cx - 0.12, 0.3, "*", "e"),
        *[Stamp(cx + 0.06 + 0.02 * (k % 2), 0.25 + 0.12 * k, "-", "t") for k in range(5)],
        *[Stamp(cx - 0.08 - 0.02 * (k % 2), 0.2 + 0.13 * k, "-", "t") for k in range(5)],
        Layer(ellipse(1.3, 0.9, 0.07, 0.035), Mat(".:+#", [(0, "d"), (0.5, "t")], outline="d"),
              sphere(1.3, 0.9, 0.07)),
    ], span=True)


def flower(cx, cy, r, petals, part, centre="w", turn=0.0):
    """A daisy-like head: petals round a centre."""
    shapes = [ellipse(cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62 * 0.9,
                      r * 0.5, r * 0.22, math.degrees(a))
              for a in [turn + 2 * math.pi * k / petals for k in range(petals)]]
    return [Layer(union(*shapes), Mat(" .:+*#", [(0, "d"), (0.35, part)], outline=part),
                  lambda x, y: 0.4 + 0.6 * min(1.0, math.hypot(x - cx, y - cy) / r)),
            Layer(circle(cx, cy, r * 0.28), Mat("o@", centre), sphere(cx, cy, r * 0.28))]


def grass(base, part="g", focus=False, seed=0, x_max=2.0):
    """A meadow's edge: a band of blades, any width."""
    top = lambda x: base - 0.05 * abs(math.sin(x * 61 + 3 * math.sin(x * 7))) - 0.02 * noise(x * 20, 0, seed)
    return Layer(below(top), Mat(" ,;'|\"", [(0, "d"), (0.4, part)], edges=False),
                 textured(0.6, 0.4, 35, seed), focus)


@scene("flowers")
def _():
    heads = [(0.55, 0.42, 0.11, 8, "e"), (0.9, 0.25, 0.13, 10, "x"), (1.25, 0.45, 0.12, 9, "a"),
             (0.72, 0.62, 0.08, 7, "t")]
    parts = [Stamp(0.25, 0.2, "}{", "x"), Stamp(1.45, 0.12, "}{", "a"),
             Layer(below(lambda x: 0.8 + 0.03 * math.sin(x * 4)), Mat(" .,", "d"), 0.6, focus=False)]
    for hx, hy, r, n, part in heads:
        stem = bezier((hx, hy), (hx + 0.06, (hy + 0.95) / 2), (hx - 0.02, 0.97))
        parts.append(Line(stem, "g"))
        mid = stem[len(stem) // 2]
        parts.append(Layer(taper(bezier(mid, (mid[0] + 0.1, mid[1] - 0.08), (mid[0] + 0.16, mid[1] - 0.02)),
                                 0.005, 0, bulge=0.04), Mat(" .:;", "g", outline="g"), 0.7))
    for hx, hy, r, n, part in heads:
        parts += flower(hx, hy, r, n, part)
    parts.append(grass(0.9))
    return Scene(1.5, parts, span=True)


@scene("jungle")
def _():
    def big_leaf(base, tip, droop, width, tone=0.7):
        mid = ((base[0] + tip[0]) / 2, min(base[1], tip[1]) - droop)
        path = bezier(base, mid, tip, 30)
        out = [Layer(taper(path, 0.01, 0.0, bulge=width),
                     Mat(" .:;+*#", [(0, "d"), (0.35, "g")], outline="g"),
                     textured(grad(base[0], base[1], tip[0], tip[1], tone, tone * 0.6), 0.1, 30))]
        out.append(Line(path[:-3], "t"))
        return out
    parts = [
        *[Line([(x + 0.025 * math.sin(k * 0.9 + x * 7), y * k / 12) for k in range(13)], "g", tone=0.5)
          for x, y in [(0.35, 0.55), (0.62, 0.38), (1.42, 0.5)]],
        *[Stamp(x + 0.025 * math.sin(k * 0.9 + x * 7) + 0.01, y * k / 12, "<" if k % 2 else ">", "g",
                tone=0.75) for x, y in [(0.35, 0.55), (0.62, 0.38), (1.42, 0.5)] for k in (3, 6, 9)],
        *[Stamp(x, y, "@", "g") for x, y in [(0.33, 0.55), (0.6, 0.38), (1.4, 0.5)]],
        Layer(below(lambda x: 0.82 + 0.05 * math.sin(x * 9) + 0.03 * math.sin(x * 23)),
              Mat(" .:;%", [(0, "d"), (0.5, "g")], edges=False), textured(0.55, 0.45, 18),
              focus=False),
    ]
    for b, t, d, w in [((1.0, 0.95), (0.55, 0.62), 0.15, 0.14), ((1.05, 0.95), (1.45, 0.62), 0.15, 0.14),
                       ((1.0, 0.95), (0.72, 0.3), 0.1, 0.12), ((1.05, 0.95), (1.3, 0.28), 0.1, 0.12),
                       ((1.02, 0.95), (1.02, 0.12), 0.0, 0.11)]:
        parts += big_leaf(b, t, d, w)
    parts += flower(0.78, 0.82, 0.07, 5, "e", "w")
    parts += [Stamp(0.45, 0.25, "{o,o}", "w"), Stamp(0.46, 0.25 + 1 / 20, "/)_)", "x"),
              Stamp(0.48, 0.25 + 2 / 20, '""', "x")]
    return Scene(1.5, parts, span=True)


@scene("blossom")
def _():
    # a bonsai-like sakura: an S-curved trunk on a round root base, under
    # one wide cloud of blossom that droops on the left and reaches far to
    # the right, flecked with red; two small clumps hang lower down
    clumps = [
        # (x, y, r): the main cloud, left to right
        (0.2, 0.45, 0.09), (0.3, 0.36, 0.11), (0.28, 0.5, 0.07), (0.42, 0.28, 0.12),
        (0.42, 0.44, 0.1), (0.55, 0.18, 0.12), (0.58, 0.35, 0.12), (0.7, 0.12, 0.11),
        (0.72, 0.28, 0.13), (0.85, 0.16, 0.12), (0.86, 0.32, 0.12), (0.98, 0.22, 0.12),
        (1.0, 0.38, 0.11), (1.1, 0.3, 0.12), (1.2, 0.38, 0.11), (1.28, 0.46, 0.1),
        (1.36, 0.53, 0.08), (1.14, 0.47, 0.08), (0.12, 0.52, 0.06), (1.43, 0.6, 0.05),
    ]
    low = [(1.06, 0.66, 0.07), (1.15, 0.64, 0.06), (1.1, 0.74, 0.05),       # lower right
           (0.66, 0.68, 0.055), (0.6, 0.72, 0.04)]                          # lower left
    rng = [(x + 0.06 * (rand(k, 3) - 0.5), y + 0.05 * (rand(k, 4) - 0.5), 0.025 + 0.02 * rand(k, 5))
           for k, (x, y, r) in enumerate(clumps * 2)]                       # ragged edge tufts

    def cloud(cs):
        return union(*[circle(x, y, r) for x, y, r in cs])
    canopy = cloud(clumps + rng)
    lower = cloud(low)

    def bloom(x, y):
        # lit from the top left, darker underneath, grainy like the petals
        t = 1.0 - (y - 0.1) * 0.75 - (x - 0.6) * 0.1
        return max(0.3, min(1.0, t + 0.3 * (noise(x * 28, y * 28, 1) - 0.5)))
    flecks = lambda x, y: noise(x * 26, y * 30, 7) > 0.72
    blossom = Mat(" .:;+*%", [(0, "a"), (0.62, "t")], outline="t")
    trunk = (bezier((0.83, 0.92), (0.74, 0.76), (0.88, 0.64), 18)
             + bezier((0.88, 0.64), (0.98, 0.52), (0.84, 0.44), 18)[1:])
    bark = Mat("|)(#%", [(0, "d"), (0.6, "w")], outline="d")
    bark_tone = lambda x, y: 0.25 + 0.3 * (math.sin(x * 120 + y * 30) > 0.3) + 0.2 * (x < 0.84)

    def build(rows):
        out = [
            # the stone it stands on, speckled, all the way across
            Layer(below(lambda x: 0.88), Mat(" .:", "d", dither=True),
                  lambda x, y: 0.25 + 0.3 * noise(x * 18, y * 40, 2), focus=False),
            Line([(-4.0, 0.885), (3.0, 0.885)], "d", "_", False, tone=0.35),
            *[Stamp(1.4 - k * 0.09 - 0.04 * rand(k, 21), 0.9 + 0.08 * rand(k, 22), ".,'*"[k % 4],
                    "aex"[k % 3], False, tone=0.4 + 0.5 * rand(k, 23)) for k in range(60)],
            # root base and trunk
            Layer(ellipse(0.83, 0.92, 0.13, 0.04), Mat(" .:%#", "d", outline="d"),
                  lambda x, y: 0.3 + 0.3 * noise(x * 40, y * 40, 3)),
            *[Line([(0.83 + dx * 0.3, 0.9), (0.83 + dx, 0.94)], "d", tone=0.2) for dx in (-0.1, -0.05, 0.06, 0.11)],
            Layer(taper(trunk, 0.1, 0.045), bark, bark_tone),
            # branches reaching out under the cloud
            *[Layer(taper(bezier(a_, m, b_), w, w * 0.4), bark, bark_tone) for a_, m, b_, w in [
                ((0.86, 0.47), (0.74, 0.44), (0.58, 0.5), 0.03),
                ((0.88, 0.5), (1.0, 0.44), (1.14, 0.5), 0.03),
                ((0.9, 0.58), (1.0, 0.6), (1.06, 0.66), 0.025),
                ((0.8, 0.6), (0.72, 0.62), (0.66, 0.68), 0.022)]],
            # the blossom, with its red flecks and frosty tips
            Layer(canopy, blossom, bloom),
            Layer(where(canopy, flecks), Mat("*%#@", [(0, "x"), (0.5, "e")], edges=False),
                  lambda x, y: 0.4 + 0.6 * noise(x * 50, y * 50, 8)),
            Layer(lower, blossom, lambda x, y: bloom(x, y - 0.25)),
            Layer(where(lower, flecks), Mat("*%#", [(0, "x"), (0.5, "e")], edges=False), 0.7),
            *[Stamp(x + r * math.cos(k) * 1.05, y + r * math.sin(k) * 1.05, "'`,.*"[k % 5], "t",
                    tone=0.9) for x, y, r in clumps for k in (1, 3, 4)],
            # petals drifting down
            *scatter(-3.0, 0.15, 0.1, 0.85, 40, ["'", ",", ".", "*"], "a", seed=97),
            *[Stamp(x, y, ch, part, tone=0.6) for x, y, ch, part in
              [(0.2, 0.7, ",", "a"), (0.45, 0.8, "'", "e"), (1.42, 0.8, ".", "a"), (0.05, 0.25, "*", "a")]],
        ]
        return out
    return Scene(1.55, build, span=True)


@scene("lavender")
def _():
    def stalk(x, base, top):
        out = [Line([(x, base), (x + 0.008, top + 0.12)], "g")]
        rows = 6
        for k in range(rows):
            y = top + 0.022 * k * 1.0
            out.append(Stamp(x - 0.012, y, ":*:" if k % 2 else "*:*", "x"))
        out.append(Stamp(x - 0.004, top - 0.03, ".", "x"))
        return out

    def field_row(y, h, part):
        top = lambda x: y - h * (0.6 + 0.4 * abs(math.sin(x * 47)))
        return Layer(Shape(lambda x, yy: top(x) <= yy <= y, (-INF, y - h, INF, y)),
                     Mat(" .:*", [(0, "d"), (0.5, part)], edges=False),
                     lambda x, yy: 0.35 + 0.6 * abs(math.sin(x * 47)) * (yy - top(x) < 0.03),
                     focus=False)
    parts = [Layer(circle(0.3, 0.22, 0.09), Mat(" .:+#", [(0, "x"), (0.5, "w")], outline="w"),
                   lambda x, y: 1 - math.hypot(x - 0.3, y - 0.22) * 8),
             Stamp(0.6, 0.12, "^v^", "d"),
             Layer(below(lambda x: 0.55 + 0.04 * math.sin(x * 3)), Mat(" .", "d", dither=True), 0.3,
                   focus=False)]
    for k, (y, h) in enumerate([(0.64, 0.05), (0.73, 0.07), (0.84, 0.09), (0.97, 0.11)]):
        parts.append(Layer(below(lambda x, y=y: y + 0.005), Mat(" .,", "g", dither=True), 0.3,
                           focus=False))
        parts.append(field_row(y, h, "x" if k % 2 == 0 else "a"))
    for x, top in [(0.85, 0.2), (0.98, 0.08), (1.1, 0.24), (1.22, 0.13), (1.34, 0.28)]:
        parts += stalk(x, 0.98, top)
    parts.append(Stamp(1.42, 0.4, "}{", "a"))
    return Scene(1.5, parts, span=True)


def peaks(base, heights, part="a", snow="t", focus=True, seed=0, snow_line=0.55):
    """A mountain range: [(x, height, half-width)], shaded light on the
    left faces and dark on the right, snow on the tops."""
    def top(x):
        y = base
        for px, h, w in heights:
            d = abs(x - px) / w
            if d < 1:
                y = min(y, base - h * (1 - d) - 0.015 * math.sin(x * 70 + px))
        return y

    def peak_at(x):
        return min(heights, key=lambda p: abs(x - p[0]) / p[2])

    def tone(x, y):
        px, h, w = peak_at(x)
        lit = 0.75 if x < px else 0.3
        return lit + 0.15 * (noise(x * 30, y * 30, seed) - 0.5)

    def snowy(x, y):
        px, h, w = peak_at(x)
        line = base - h * snow_line + 0.03 * math.sin(x * 50)
        return y < line
    mountain = below(top)
    rock = Mat(" .:-=+#", [(0, "d"), (0.5, part)], outline=part)
    # the peaks are the focus; the flat ground under them is background
    return [Layer(where(mountain, lambda x, y: y > base), rock, tone, False),
            Layer(where(mountain, lambda x, y: y <= base), rock, tone, focus),
            Layer(where(mountain, snowy), Mat(" .:*#", [(0, "d"), (0.5, snow)], outline=snow),
                  tone, focus)]


def where(shape, fn):
    """The part of a shape where fn(x, y) holds."""
    return Shape(lambda x, y: shape.test(x, y) and fn(x, y), shape.box)


@scene("snowpeaks")
def _():
    parts = [*scatter(0.0, 0.0, 1.5, 0.95, 30, ["*", ".", "'", "+"], "t", seed=17)]
    parts += peaks(0.85, [(x, 0.25 + 0.15 * rand(i, 2), 0.25) for i, x in
                          enumerate([1.6 - k * 0.22 for k in range(20)])], "d", "d", False, 1)
    parts += peaks(0.95, [(1.05, 0.85, 0.5), (0.65, 0.55, 0.35), (1.4, 0.6, 0.3)], "a", "t", True, 2)
    parts.append(Layer(below(lambda x: 0.95), Mat(" .:", [(0, "d"), (0.5, "t")], edges=False),
                       0.6, focus=False))
    return Scene(1.5, parts, span=True)


@scene("reef")
def _():
    def fish(x, y, size, part, flip=False):
        d = -1 if flip else 1
        body = ellipse(x, y, size, size * 0.55)
        tail = poly([(x - d * size * 0.8, y), (x - d * size * 1.5, y - size * 0.5),
                     (x - d * size * 1.5, y + size * 0.5)])
        return [Layer(body | tail, Mat(" .:+*#", [(0, "d"), (0.4, part)], outline=part),
                      sphere(x, y, size)),
                Stamp(x + d * size * 0.5 - 0.01, y - size * 0.15, "o", "t")]

    def coral(x, base, h, part, seed):
        """Branching coral: forks that split twice, with round tips."""
        out = []

        def branch(x0, y0, angle, length, depth, k):
            x1 = x0 + math.cos(angle) * length * 0.5
            y1 = y0 - math.sin(angle) * length
            out.append(Line([(x0, y0), (x1, y1)], part))
            if depth == 0:
                out.append(Stamp(x1 - 0.008, y1 - 0.03, "o@*"[k % 3], part))
                return
            for side in (-1, 1):
                branch(x1, y1, angle + side * (0.45 + 0.2 * rand(k + side, seed)),
                       length * 0.7, depth - 1, k * 2 + (side > 0))
        branch(x, base, math.pi / 2, h * 0.4, 2, 1)
        return out
    parts = [*[Stamp(x, y, "o", "t", False) for x, y in [(0.3, 0.2), (0.33, 0.12), (0.31, 0.05),
                                                      (1.35, 0.3), (1.37, 0.22)]],
             *[Line([(x + 0.018 * math.sin(j * 1.4 + x * 9), 0.95 - h * j / 8) for j in range(9)],
                    "g", focus=False, tone=0.5)
               for i, (x, h) in enumerate((1.6 - k * 0.27, 0.15 + 0.2 * rand(k, 4)) for k in range(22))],
             Layer(below(lambda x: 0.9 + 0.03 * math.sin(x * 8)), Mat(" .:,", [(0, "d"), (0.5, "w")],
                   edges=False), textured(0.5, 0.4, 30), focus=False)]
    parts += coral(1.2, 0.93, 0.75, "e", 1)
    parts += coral(0.78, 0.93, 0.55, "x", 2)
    parts += coral(1.45, 0.93, 0.45, "g", 3)
    parts.append(Layer(ellipse(0.98, 0.9, 0.1, 0.07) & rect(0, 0, 9, 0.92),
                       Mat(" ~=%", [(0, "d"), (0.4, "w")], outline="w"),
                       lambda x, y: 0.5 + 0.5 * math.sin(x * 120 + y * 40)))

    def with_fish(rows):
        big = [r"      _,--._",
               r" |\ .'  .   `.",
               r" | >  (  (   o)",
               r" |/ `.  '   .'",
               r"      `--''"]
        out = list(parts)
        if rows >= 14:
            out += lines_at(int(0.25 * 2 * rows), int(rows * 0.15), rows, big,
                            {"o": "t", "|": "x", "\\": "x", "/": "x", ">": "x", "": "w"})
            out += lines_at(int(1.15 * 2 * rows), int(rows * 0.42), rows, ["<'))))><"], "a")
            out += lines_at(int(0.75 * 2 * rows), int(rows * 0.05), rows, ["><(('>"], "x")
        else:
            out += lines_at(int(0.3 * 2 * rows), 1, rows, ["><((('>"], "w")
            out += lines_at(int(1.1 * 2 * rows), 3, rows, ["<'))><"], "a")
        return out
    return Scene(1.5, with_fish, span=True)


@scene("volcano")
def _():
    cx = 1.0

    def cone_top(x):
        d = abs(x - cx)
        return 0.3 + (d - 0.1) * 1.4 if d > 0.1 else 0.3 + 0.02 * math.sin(x * 80)
    cone = below(cone_top, cx - 0.65, cx + 0.65)
    flows = [bezier((cx - 0.05, 0.31), (cx - 0.12, 0.55), (cx - 0.25, 0.85)),
             bezier((cx + 0.04, 0.31), (cx + 0.1, 0.5), (cx + 0.08, 0.8)),
             bezier((cx, 0.31), (cx + 0.2, 0.6), (cx + 0.38, 0.86))]
    smoke = union(*[circle(cx + dx, y, r) for dx, y, r in
                    [(0.0, 0.2, 0.07), (0.06, 0.12, 0.08), (-0.04, 0.05, 0.09), (0.14, 0.04, 0.07),
                     (0.24, 0.07, 0.06)]])
    return Scene(1.5, [
        Layer(smoke, Mat(" .:oO@", [(0, "d"), (0.6, "t")], outline="d"), textured(0.5, 0.3, 20)),
        Layer(cone, Mat(" .:-=+#", [(0, "d"), (0.45, "x")], outline="x"),
              textured(lambda x, y: 0.75 if x < cx else 0.35, 0.15, 30)),
        *[Layer(taper(f, 0.035, 0.015), Mat("~=*#", [(0, "e"), (0.6, "w")], edges=False),
                lambda x, y: 0.5 + 0.5 * math.sin(y * 90)) for f in flows],
        Layer(ellipse(cx, 0.31, 0.09, 0.02), Mat("#@", "w"), 1.0),
        *scatter(0.7, 0.0, 1.3, 0.28, 10, ["*", "'", "."], "w", seed=19),
        Layer(below(lambda x: 0.88 + 0.02 * math.sin(x * 9)),
              Mat(" .:~=", [(0, "d"), (0.55, "e"), (0.85, "w")], edges=False),
              lambda x, y: 0.4 + 0.6 * max(0.0, math.sin(x * 23 + y * 50) * math.sin(x * 7)),
              focus=False),
    ], span=True)


# ---------------------------------------------------------------- batch 3

@scene("bamboo")
def _():
    def stalk(x, top, w, focus=True, part="g", lean=0.0):
        out = [Layer(taper([(x, 1.02), (x + lean, top)], w, w * 0.8),
                     Mat(" :|#", [(0, "d"), (0.4, part)], outline=part),
                     lambda px, py: 0.85 if px < x + lean * (1.02 - py) else 0.45, focus)]
        y = 0.95
        while y > top + 0.05:
            xx = x + lean * (1.02 - y) / (1.02 - top)
            out.append(Line([(xx - w * 0.7, y), (xx + w * 0.7, y)], "t", "=", focus))
            y -= 0.13 + 0.02 * math.sin(x * 40)
        return out

    def leaves(x, y, side, focus=True):
        return [Layer(taper(bezier((x, y), (x + side * 0.1, y - 0.03), (x + side * 0.22, y + 0.05)),
                            0.005, 0, bulge=0.035), Mat(" .:;", "g", outline="g"), 0.7, focus)
                for y in (y, y + 0.05)]
    parts = [Layer(circle(0.3, 0.2, 0.09), Mat(" .:+#", [(0, "x"), (0.5, "w")], outline="w"),
                   lambda x, y: 1 - math.hypot(x - 0.3, y - 0.2) * 8)]
    for i in range(28):
        x = 1.6 - i * 0.14 - rand(i, 7) * 0.06
        parts.append(Line([(x, 1.0), (x + 0.01, 0.3 + 0.25 * rand(i, 8))], "d", "|", focus=False))
        for y in (0.5, 0.75):
            parts.append(Stamp(x - 0.004, y + 0.05 * rand(i, 9), "+", "d", False))
    parts += stalk(0.85, -0.05, 0.05, lean=0.03)
    parts += stalk(1.05, 0.1, 0.06, lean=-0.02)
    parts += stalk(1.27, -0.05, 0.045, lean=0.04)
    parts += leaves(0.88, 0.25, -1) + leaves(1.06, 0.45, 1) + leaves(1.29, 0.2, 1) + leaves(0.86, 0.6, 1)
    parts.append(Layer(below(lambda x: 0.95), Mat(" .,;", [(0, "d"), (0.5, "g")], edges=False),
                       textured(0.6, 0.3, 30), focus=False))
    return Scene(1.5, parts, span=True)


@scene("bat")
def _():
    mx, my, mr = 1.0, 0.36, 0.3

    def moon_tone(x, y):
        t = 0.75 + 0.25 * (noise(x * 14, y * 14, 4) - 0.5) * 2
        for kx, ky, kr in [(0.9, 0.3, 0.06), (1.1, 0.45, 0.05), (1.12, 0.22, 0.035)]:
            if math.hypot(x - kx, y - ky) < kr:
                t -= 0.3
        return t
    wing = [(0, 0), (0.08, -0.06), (0.2, -0.1), (0.32, -0.08), (0.42, -0.02), (0.36, 0.0),
            (0.33, 0.06), (0.27, 0.03), (0.22, 0.08), (0.16, 0.04), (0.1, 0.07), (0.05, 0.02)]
    bx, by = 0.95, 0.38
    right = poly([(bx + 0.03 + x, by + y) for x, y in wing])
    left = poly([(bx - 0.03 - x, by + y) for x, y in wing])
    body = ellipse(bx, by + 0.02, 0.045, 0.06) | circle(bx, by - 0.05, 0.035) \
        | poly([(bx - 0.035, by - 0.06), (bx - 0.03, by - 0.13), (bx - 0.01, by - 0.07)]) \
        | poly([(bx + 0.035, by - 0.06), (bx + 0.03, by - 0.13), (bx + 0.01, by - 0.07)])

    def castle_top(x):
        towers = [(0.35, 0.55, 0.04), (0.5, 0.62, 0.05), (0.2, 0.66, 0.03), (-0.6, 0.6, 0.04)]
        y = 0.72 + 0.03 * math.sin(x * 5)
        for tx, ty, tw in towers:
            if abs(x - tx) < tw:
                y = ty if abs(x - tx) < tw * 0.85 else min(y, ty + 0.03)
            if abs(x - tx) < tw * 0.4:
                y = min(y, ty - 0.08 * (1 - abs(x - tx) / (tw * 0.4)))
        return y
    return Scene(1.45, [
        *scatter(0.0, 0.0, 1.45, 0.6, 18, ["*", ".", "+", "'"], "t", seed=23),
        Layer(circle(mx, my, mr), Mat(" .:-=+*#", [(0, "d"), (0.45, "w")], outline="w"), moon_tone),
        Layer(right | left | body, Mat("#", "d", outline="a"), 0.9),
        Stamp(bx - 0.03, by - 0.05, "^ ^", "e"),
        Stamp(0.3, 0.25, "^v^", "a"), Stamp(0.15, 0.4, "v", "a"),
        Layer(where(below(castle_top), lambda x, y: y <= 0.8), Mat(" .:#", [(0, "d"), (0.6, "a")], outline="a"),
              lambda x, y: 0.55 + 0.2 * (math.sin(x * 140) > 0.6) * (math.sin(y * 140) > 0), focus=False),
        Layer(where(below(castle_top), lambda x, y: y > 0.8), Mat(" .:", "d", dither=True), 0.35,
              focus=False),
        *[Stamp(x, y, "o", "w", False) for x, y in [(0.5, 0.68), (0.35, 0.62), (0.51, 0.75)]],
    ], span=True)


@scene("mountains")
def _():
    parts = [*scatter(0.0, 0.0, 1.5, 0.45, 16, ["*", ".", "+"], "t", seed=29),
             Layer(circle(0.35, 0.18, 0.07), Mat(" .:+#", "t", outline="t"), 0.8)]
    parts += peaks(0.7, [(1.6 - k * 0.3, 0.3 + 0.12 * rand(k, 31), 0.28) for k in range(12)],
                   "d", "d", False, 3, 0.4)
    parts += peaks(0.85, [(0.55, 0.42, 0.3)], "a", "t", False, 4)
    parts += peaks(0.85, [(1.15, 0.7, 0.42), (1.45, 0.5, 0.3)], "a", "t", True, 4)
    parts.append(Layer(below(treeline(0.97, 0.18, 0.04, 5)), Mat(" .:", "d", outline="g"), 0.5,
                       focus=False))
    return Scene(1.5, parts, span=True)


@scene("coffee")
def _():
    cx = 0.7
    cup = (rect(cx - 0.28, 0.4, cx + 0.28, 0.72) | ellipse(cx, 0.72, 0.28, 0.12)) & rect(-9, 0.4, 9, 0.83)
    handle = ring(cx + 0.33, 0.56, 0.06, 0.1)

    def cyl(x, y):
        u = (x - cx) / 0.28
        return max(0.1, min(1.0, 0.95 - abs(u + 0.4) * 0.7))
    steam = [bezier((cx + dx, 0.34), (cx + dx + 0.08, 0.2), (cx + dx - 0.02, 0.04), 10)
             for dx in (-0.12, 0.0, 0.12)]

    def build(rows):
        return [
            *desk(rows),
            *[Line(sx, "d", tone=0.4 + 0.1 * k) for k, sx in enumerate(steam)],
            Layer(ellipse(cx, 0.85, 0.45, 0.07), Mat(" .:=#", [(0, "d"), (0.5, "t")], outline="t"),
                  grad(cx - 0.4, 0.82, cx + 0.4, 0.88, 0.9, 0.3)),
            Layer(handle, Mat(" :#", "x", outline="x"), 0.6),
            Layer(cup, Mat(" .:-=+*#", [(0, "d"), (0.4, "x"), (0.8, "t")], outline="x"), cyl),
            Layer(ellipse(cx, 0.4, 0.28, 0.06), Mat(" .:", "t", outline="t"), 0.6),
            Layer(ellipse(cx, 0.405, 0.24, 0.042), Mat("~=%", [(0, "e"), (0.5, "w")], edges=False),
                  lambda x, y: 0.5 + 0.4 * math.sin(x * 60)),
            Stamp(cx - 0.06, 0.58, "<3", "e"),
            *[Stamp(x, 1 - 1.5 / rows, "()", "w", False, tone=0.5) for x in (0.12, 0.2, -0.6, -1.4, 1.2)],
        ]
    return Scene(1.3, build, span=True)


@scene("sun")
def _():
    cx, cy, r = 0.7, 0.4, 0.21
    rays = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        long = 1.7 if k % 2 == 0 else 1.4
        rays.append(Line([(cx + math.cos(a) * r * 1.18, cy + math.sin(a) * r * 1.18),
                          (cx + math.cos(a) * r * long, cy + math.sin(a) * r * long)],
                         "w" if k % 2 == 0 else "x", tone=0.8 if k % 2 == 0 else 0.5))
    return Scene(1.4, [
        *hills(0.86, "g", 2),
        *rays,
        Layer(ring(cx, cy, r * 1.02, r * 1.12), Mat(" .:", "x", edges=False), 0.6),
        Layer(circle(cx, cy, r), Mat(" .:-=+*#%@", [(0, "e"), (0.4, "x"), (0.7, "w")], outline="w"),
              sphere(cx, cy, r, -0.4, -0.5, 0.25, 1.0)),
        Layer(circle(1.25, 0.15, 0.05), Mat(" .:+#", [(0, "d"), (0.5, "a")], outline="a"),
              sphere(1.25, 0.15, 0.05, -0.9, -0.3, 0.1, 1.0)),
        Stamp(0.1, 0.12, "*", "t"), Stamp(1.3, 0.45, "+", "t"), Stamp(0.08, 0.5, ".", "t"),
        Stamp(0.25, 0.3, "v", "d"), Stamp(1.15, 0.6, "^v^", "d"),
    ], span=True)


@scene("code")
def _():
    code = [
        "def type_fast(words):",
        "    for word in words:",
        "        if word.strip():",
        "            yield word",
        "    return \"done\"  # :)",
        "",
        "score = wpm * accuracy",
        "best = max(best, score)",
        "streak += 1",
        "print(f\"{score:.1f}\")",
        "# keep going",
    ]
    kw = {"def", "for", "in", "if", "return", "yield"}
    width = 34

    def colour(line):
        out = []
        for tok in re.findall(r"\s+|\w+|\"[^\"]*\"|#.*|.", line):
            if tok.strip() == "":
                c = " "
            elif tok in kw:
                c = "e"
            elif tok.startswith('"'):
                c = "w"
            elif tok.startswith("#"):
                c = "d"
            elif tok in ("type_fast", "print", "strip", "max"):
                c = "g"
            elif tok.isdigit():
                c = "x"
            elif re.match(r"\w", tok):
                c = "t"
            else:
                c = "a"
            out.append(c * len(tok))
        return "".join(out)

    def editor(rows):
        n = {26: 11, 20: 8, 14: 5, 10: 2}[rows]
        top = rows - 2 - (n + 4) - (1 if rows > 10 else 0)
        out = desk(rows)
        out += lines_at(0, top, rows, [
            "." + "-" * width + ".",
            "| o o o" + " " * (width - 18) + "minitype.py |",
            "|" + "-" * width + "|"], {"o": "e", "": "d"})
        out[-2].part = "dde w gd"
        for i in range(n):
            line = code[i]
            body = f"{i + 1:>2} " + line
            out += lines_at(0, top + 3 + i, rows, ["|" + body.ljust(width) + "|"],
                            ["dddd" + colour(line).ljust(width - 3) + "d"])
        out += lines_at(0, top + 3 + n, rows, ["'" + "-" * width + "'"], "d")
        cx, cy = at(4 + len(code[n - 1]) + 1, top + 2 + n, rows)
        out.append(Stamp(cx, cy, "_", "a", tone=0.95))
        return out
    return Scene(lambda rows: (width + 4) / (2 * rows), editor, span=True)


@scene("cat")
def _():
    cx = 0.75
    body = ellipse(cx, 0.66, 0.22, 0.24)
    head = circle(cx - 0.02, 0.32, 0.14)
    ears = poly([(cx - 0.14, 0.29), (cx - 0.13, 0.11), (cx - 0.04, 0.21)]) | \
        poly([(cx + 0.1, 0.29), (cx + 0.09, 0.11), (cx, 0.21)])
    tail = taper(bezier((cx + 0.18, 0.83), (cx + 0.45, 0.83), (cx + 0.38, 0.53)), 0.06, 0.035)
    fur = textured(lambda x, y: 0.85 - (x - cx + 0.2) * 1.2, 0.12, 30)

    def boards(x, y):
        return 0.3 + 0.4 * ((x * 4) % 1 > 0.05) + 0.15 * math.sin(x * 40 + y * 5)
    return Scene(1.3, [
        *scatter(-2.0, 0.0, 1.3, 0.8, 30, ["*", "+", "."], "w", seed=31),
        Layer(below(lambda x: 0.92), Mat(" .-=", [(0, "d"), (0.6, "x")], edges=False), boards,
              focus=False),
        Line([(-4.0, 0.925), (3.0, 0.925)], "x", "_", False, tone=0.8),
        Layer(tail, Mat(" .:;+*#", [(0, "d"), (0.45, "a")], outline="a"), fur),
        Layer(body, Mat(" .:;+*#%", [(0, "d"), (0.45, "a")], outline="a"), fur),
        Layer(ellipse(cx - 0.02, 0.7, 0.1, 0.15), Mat(" .:", "t"), 0.7),
        Layer(head | ears, Mat(" .:;+*#%", [(0, "d"), (0.45, "a")], outline="a"), fur),
        Layer(poly([(cx - 0.12, 0.27), (cx - 0.115, 0.16), (cx - 0.07, 0.225)]), Mat(":", "e"), 0.6),
        Layer(poly([(cx + 0.08, 0.27), (cx + 0.075, 0.16), (cx + 0.03, 0.225)]), Mat(":", "e"), 0.6),
        Stamp(cx - 0.09, 0.31, "o", "g", tone=0.9), Stamp(cx + 0.03, 0.31, "o", "g", tone=0.9),
        Stamp(cx - 0.035, 0.38, "w", "e"),
        Stamp(cx - 0.23, 0.37, "=", "t"), Stamp(cx + 0.14, 0.37, "=", "t"),
        Layer(ellipse(cx - 0.1, 0.9, 0.07, 0.035) | ellipse(cx + 0.06, 0.9, 0.07, 0.035),
              Mat(" .:+", [(0, "d"), (0.5, "a")], outline="a"), 0.7),
        Layer(circle(0.25, 0.83, 0.09), Mat(" .:@", [(0, "d"), (0.5, "e")], outline="e"),
              lambda x, y: 0.5 + 0.5 * math.sin((x - y) * 70)),
        Line(bezier((0.31, 0.86), (0.45, 0.96), (cx - 0.15, 0.92), 8), "e"),
    ], span=True)


@scene("rain")
def _():
    glyphs = "0123456789ABCDEFXZ$#@%&*+=<>?"

    def columns(rows):
        out = []
        cw = 0.5 / rows
        for i in range(int(1.6 / cw / 2) + 120):
            x = 1.55 - i * cw * 2
            if x < -3.5:
                break
            length = 3 + int(rand(i, 41) * rows * 0.7)
            head = int(rand(i, 42) * (rows + length)) - 2
            focus = x > 0.5
            for k in range(length):
                r = head - k
                if 0 <= r < rows:
                    ch = glyphs[int(rand(i * 31 + r, 43) * len(glyphs))]
                    part = "t" if k == 0 else ("g" if k < length * 0.6 else "d")
                    out.append(Stamp(x, (r + 0.5) / rows, ch, part, focus))
        return out
    return Scene(1.6, columns, span=True)


# ---------------------------------------------------------------- batch 4

@scene("monitor")
def _():
    screens = {26: ["READY.", "> LOAD \"TYPE\",8,1", "SEARCHING FOR TYPE", "LOADING",
                    "READY.", "> RUN", "", "WPM 112  ACC 98%", "> _"],
               20: ["READY.", "> LOAD \"TYPE\",8,1", "SEARCHING FOR TYPE", "LOADING",
                    "> RUN", "WPM 112  ACC 98%", "> _"],
               14: ["> LOAD \"TYPE\",8,1", "LOADING", "> RUN", "> _"],
               10: ["> RUN", "> _"]}
    w = 26

    def crt(rows):
        screen = screens[rows]
        n = len(screen)
        stand = rows > 10
        kb = rows >= 20
        height = n + 5 + (2 if stand else 0) + (3 if kb else 0)
        top = rows - 2 - height
        out = desk(rows)
        out += lines_at(0, top, rows, [" ." + "-" * (w + 4) + ". ",
                                       " | ." + "-" * w + ". | "], "d")
        for i, line in enumerate(screen):
            out += lines_at(0, top + 2 + i, rows, [" | | " + line.ljust(w - 2) + " | | "],
                            ["d" * 5 + "w" * (w - 2) + "d" * 5])
            out[-1].tone = 0.85
        foot = [" | '" + "-" * w + "' | ", " |  " + " " * (w - 6) + "[] o== | ", " '" + "-" * (w + 4) + "' "]
        if stand:
            foot += ["     ____|_______|____     ", "    [___________________]  "]
        out += lines_at(0, top + 2 + n, rows, foot, ["d", "d" * (w - 2) + "ddeddd", "d", "d", "d"])
        if kb:
            out += lines_at(0, top + 2 + n + len(foot), rows,
                            ["   .=====================.  ",
                             "  /_/_/_/_/_/_/_/_/_/_/_/_\\ ",
                             " '-------------------------'"], "d")
        return out
    return Scene(lambda rows: (w + 8) / (2 * rows), crt, span=True)


@scene("plane")
def _():
    # a paper plane gliding left to right, a dotted trail looping behind it
    nose = (1.32, 0.3)
    wing_top, fold, wing_low, keel = (0.72, 0.1), (0.9, 0.36), (0.78, 0.54), (0.98, 0.44)
    trail = (bezier((0.86, 0.38), (0.5, 0.5), (0.36, 0.36), 18)
             + bezier((0.36, 0.36), (0.26, 0.2), (0.4, 0.22), 10)[1:]
             + bezier((0.4, 0.22), (0.55, 0.3), (0.1, 0.62), 18)[1:])
    parts = [Line(trail[i:i + 2], "d", ".", tone=0.3 + 0.5 * i / len(trail))
             for i in range(0, len(trail) - 1, 2)]
    for x, y, r in [(0.48, 0.84, 0.17), (1.12, 0.8, 0.13), (-0.5, 0.82, 0.2), (-1.4, 0.86, 0.22),
                    (-2.4, 0.8, 0.18), (-3.3, 0.84, 0.2)]:
        puff = union(circle(x - r * 0.5, y, r * 0.45), circle(x, y - r * 0.2, r * 0.6),
                     circle(x + r * 0.55, y, r * 0.4), rect(x - r * 0.9, y, x + r * 0.9, y + r * 0.35))
        parts.append(Layer(puff & rect(-INF, -INF, INF, y + r * 0.3),
                           Mat(" .:-=", [(0, "d"), (0.45, "t")], outline="t"),
                           grad(x, y - r, x, y + r * 0.3, 0.95, 0.25), focus=x > 0))
    parts += [
        # the far wing, in shadow, then the near one lit, then the keel
        Layer(poly([nose, fold, wing_low]), Mat(" .:-=+", [(0, "d"), (0.4, "a")], outline="a"), 0.4),
        Layer(poly([nose, wing_top, fold]), Mat(" .:-=+*", [(0, "d"), (0.4, "t")], outline="t"),
              grad(0.75, 0.15, 1.3, 0.3, 0.95, 0.6)),
        Layer(poly([nose, fold, keel]), Mat(" .:-", [(0, "d"), (0.5, "a")], outline="d"), 0.25),
        Line([nose, fold], "d", tone=0.3),
        Stamp(0.15, 0.1, "~", "d"), Stamp(1.42, 0.6, "~", "d"), Stamp(0.6, 0.06, "v", "d"),
    ]
    return Scene(1.5, parts, span=True)


@scene("bolt")
def _():
    bolt = poly([(0.82, 0.02), (0.55, 0.5), (0.74, 0.5), (0.5, 0.94), (1.02, 0.38), (0.8, 0.38),
                 (1.02, 0.02)])
    glow = poly([(0.78, -0.03), (0.47, 0.55), (0.66, 0.55), (0.42, 1.0), (1.12, 0.33), (0.9, 0.33),
                 (1.1, -0.03)])
    small = [poly([(x, y), (x - 0.08, y + 0.14), (x - 0.03, y + 0.14), (x - 0.1, y + 0.28),
                   (x + 0.04, y + 0.1), (x - 0.01, y + 0.1), (x + 0.04, y)])
             for x, y in [(0.25, 0.2), (1.3, 0.45), (-0.9, 0.3), (-2.2, 0.25)]]
    return Scene(1.4, [
        *rain(120, 91),
        Layer(below(lambda x: 0.9 + 0.03 * math.sin(x * 4) + 0.015 * math.sin(x * 17)),
              Mat(" .:", "d"), 0.45, focus=False),
        Layer(glow, Mat(" .:", "d", dither=True), 0.5),
        Layer(bolt, Mat(" .:-=+*#%@", [(0, "a"), (0.6, "t")], outline="a"),
              grad(1.0, 0.05, 0.5, 0.95, 1.0, 0.45)),
        *[Layer(sh, Mat(" :+#", "a", outline="a"), 0.6, focus=sh.box[0] > 0) for sh in small],
        Stamp(0.6, 0.15, "*", "t"), Stamp(1.1, 0.75, "+", "t"), Stamp(0.3, 0.7, ".", "t"),
    ], span=True)


@scene("rainbow")
def _():
    cx, cy = 0.75, 0.84
    bands = ["e", "x", "w", "g", "a", "t"]
    parts = []
    for k, part in enumerate(bands):
        r1 = 0.68 - k * 0.075
        parts.append(Layer(ring(cx, cy, r1 - 0.075, r1, cy), Mat(" :=#", part, edges=False),
                           lambda x, y: 0.55 + 0.45 * math.sin(x * 25 + y * 9) ** 2))
    parts.append(grass(0.92))
    for x, y, r in [(0.14, 0.82, 0.14), (1.36, 0.82, 0.14)]:
        puff = union(circle(x - r * 0.5, y, r * 0.5), circle(x + r * 0.1, y - r * 0.35, r * 0.6),
                     circle(x + r * 0.6, y, r * 0.45), rect(x - r, y, x + r, y + r * 0.4))
        parts.append(Layer(puff, Mat(" .:oO", [(0, "d"), (0.5, "t")], outline="t"),
                           grad(x, y - r, x, y + r * 0.4, 1.0, 0.3)))
    parts += scatter(-3.0, 0.0, 1.5, 0.5, 30, ["*", "+", "'"], "w", seed=37)
    parts += [Stamp(-0.2 - k * 0.37, 0.89, "*o@"[k % 3], "ewxa"[k % 4], False) for k in range(12)]
    return Scene(1.5, parts, span=True)


@scene("party")
def _():
    balloons = [(0.95, 0.28, 0.12, "e"), (1.18, 0.22, 0.11, "a"), (1.38, 0.32, 0.1, "g"),
                (0.78, 0.42, 0.1, "w")]
    parts = scatter(-3.0, 0.0, 1.5, 1.0, 120, ["*", ".", "'", "o", "+", ",", "~"], "extawg"[0], seed=41)
    for k, st in enumerate(parts):
        st.part = "exawgt"[k % 6]
    for x, y, r, part in balloons:
        parts.append(Line(bezier((x, y + r * 1.1), (x + 0.05, y + 0.35), (1.05, 0.95), 12), "d"))
    for x, y, r, part in balloons:
        parts.append(Layer(ellipse(x, y, r * 0.85, r) | poly([(x - 0.02, y + r * 1.1), (x + 0.02, y + r * 1.1),
                                                              (x, y + r * 0.95)]),
                           Mat(" .:-=+*#%", [(0, "d"), (0.3, part), (0.92, "t")], outline=part),
                           sphere(x, y, r, -0.6, -0.7, 0.2, 1.0)))
    gx, gy, gw, gh = 0.48, 0.72, 0.17, 0.24
    parts += [
        Layer(rect(gx - gw, gy, gx + gw, gy + gh), Mat(" .:+*#", [(0, "d"), (0.4, "x")], outline="x"),
              grad(gx - gw, gy, gx + gw, gy + gh, 0.9, 0.35)),
        Layer(rect(gx - gw - 0.015, gy - 0.05, gx + gw + 0.015, gy + 0.01),
              Mat(" .:+*#", [(0, "d"), (0.4, "x")], outline="x"), 0.8),
        Layer(rect(gx - 0.022, gy - 0.05, gx + 0.022, gy + gh), Mat("|#", "w"), 0.85),
        Layer(rect(gx - gw, gy + gh * 0.4, gx + gw, gy + gh * 0.4 + 0.035), Mat("=#", "w"), 0.7),
        Layer(ellipse(gx - 0.06, gy - 0.08, 0.06, 0.035, 20) | ellipse(gx + 0.06, gy - 0.08, 0.06, 0.035, -20),
              Mat(" .:o@", "w", outline="w"), 0.8),
    ]
    return Scene(1.5, parts, span=True)


@scene("glitch")
def _():
    texts = {26: ["SYSTEM ERROR 0xDEAD", "", "  > type_test.exe", "  [FAIL] segfault",
                  "  core dumped @ 0x7f", "  stack: 0x00 0xff 0x1e", "", "  reboot? [y/n] _", "",
                  "  ##########--- 72%", "  ######-------- 41%", ""],
             20: ["SYSTEM ERROR 0xDEAD", "", "  > type_test.exe", "  [FAIL] segfault",
                  "  core dumped @ 0x7f", "", "  retry? [y/n] _", "", "  ##########--- 72%"],
             14: ["SYSTEM ERROR", "", "  > type_test.exe", "  [FAIL] segfault", "  retry? [y/n] _"],
             10: ["ERROR", "  [FAIL]", "  retry? _"]}
    w = 30

    def scan(x, y):
        band = math.floor(y * 40)
        on = rand(math.floor(x * (6 + band % 5) + band * 3), 57) > 0.45
        return (0.3 + 0.7 * rand(math.floor(x * 30) + band * 101, 58)) if on else 0.0

    def screen(rows):
        lines = texts[rows]
        top = rows - 3 - (len(lines) + 2)
        out = [Layer(below(lambda x: (rows - 3 + 0.02) / rows),
                     Mat(" .-=#%", [(0, "d"), (0.5, "e"), (0.8, "x")], edges=False), scan, focus=False)]
        out += lines_at(0, top, rows, ["#" + "=" * w + "#"], "e")
        for i, line in enumerate(lines):
            shift = int(rand(i, 51) * 4) - 1 if rand(i, 52) > 0.6 else 0
            row = "|" + (" " * max(0, shift) + line).ljust(w)[:w] + "|"
            p = "e" + ("e" if "ERR" in line or "FAIL" in line else "a") * w + "e"
            out += lines_at(0, top + 1 + i, rows, [row], [p])
        out += lines_at(0, top + 1 + len(lines), rows, ["#" + "=" * w + "#"], "e")
        for k in range(rows // 2):
            r = top + int(rand(k, 53) * (len(lines) + 2))
            c = int(rand(k, 54) * (w + 6)) - 3
            bar = "".join("#%@$&*!?/\\=+~"[int(rand(k * 9 + j, 55) * 13)]
                          for j in range(3 + int(rand(k, 56) * 8)))
            x, y = at(c, r, rows)
            out.append(Stamp(x, y, bar, "extg"[k % 4], tone=0.4 + 0.5 * rand(k, 60)))
        return out
    return Scene(lambda rows: (w + 8) / (2 * rows), screen, span=True)


@scene("bubbles")
def _():
    bubbles = [(1.0, 0.45, 0.2), (0.62, 0.27, 0.12), (1.32, 0.2, 0.1), (0.72, 0.68, 0.08),
               (1.35, 0.66, 0.09), (0.45, 0.55, 0.05), (1.15, 0.8, 0.05), (0.9, 0.1, 0.06)]
    parts = [Layer(below(lambda x: 0.9 + 0.025 * math.sin(x * 21) + 0.015 * math.sin(x * 47)),
                   Mat(" .oO@", [(0, "d"), (0.5, "t")], edges=False),
                   lambda x, y: 0.3 + 0.7 * noise(x * 40, y * 40, 5), focus=False)]
    parts += scatter(-3.5, 0.55, 0.3, 0.9, 50, ["o", ".", "O", "."], "aexg", seed=61)
    for i, (x, y, r) in enumerate(bubbles):
        part = "aexg"[i % 4]
        parts.append(Layer(ring(x, y, r * 0.78, r), Mat(" .:oO", [(0, "d"), (0.5, part)], outline=part),
                           lambda px, py, x=x, y=y: 0.95 - 0.5 * ((px - x) + (py - y)) / 0.2))
        parts.append(Layer(ellipse(x - r * 0.4, y - r * 0.45, r * 0.22, r * 0.12, -40), Mat("o@", "t"), 0.95))
    parts += scatter(0.3, 0.0, 1.5, 0.85, 30, ["o", ".", "o", "."], "d", seed=59)
    return Scene(1.5, parts, span=True)


# ---------------------------------------------------------------- batch 5

@scene("aurora")
def _():
    def curtain(y0, amp, freq, phase, depth, part):
        top = lambda x: y0 + amp * math.sin(x * freq + phase) + 0.03 * math.sin(x * 11 + phase)
        band = Shape(lambda x, y: top(x) <= y <= top(x) + depth, (-INF, 0, INF, 1))
        tone = lambda x, y: max(0.0, (1 - (y - top(x)) / depth) * (0.55 + 0.45 * math.sin(x * 90 + phase) ** 2))
        return Layer(band, Mat(" .:|!", [(0, "d"), (0.35, part)], edges=False), tone, focus=False)
    parts = [
        *scatter(-3.0, 0.0, 1.5, 0.75, 60, ["*", ".", "'", "+", "."], "t", seed=61),
        curtain(0.08, 0.06, 2.3, 0.0, 0.28, "g"),
        curtain(0.18, 0.05, 3.1, 2.0, 0.22, "a"),
        curtain(0.3, 0.04, 1.7, 4.0, 0.16, "x"),
    ]
    parts += peaks(0.85, [(1.6 - k * 0.27, 0.22 + 0.12 * rand(k, 63), 0.26) for k in range(18)],
                   "d", "t", False, 6, 0.4)
    parts.append(Layer(below(treeline(0.97, 0.2, 0.045, 7)), Mat(" .:", "d"), 0.6, focus=False))
    # a cabin with a lit window
    cabin = rect(0.98, 0.78, 1.22, 0.95)
    roof = poly([(0.94, 0.8), (1.1, 0.66), (1.26, 0.8)])
    parts += [
        Layer(cabin, Mat(" .:=#", [(0, "d"), (0.5, "w")], outline="d"),
              lambda x, y: 0.4 + 0.3 * (math.sin(y * 300) > 0)),
        Layer(roof, Mat(" .:#", [(0, "d"), (0.6, "t")], outline="t"), 0.7),
        Layer(rect(1.13, 0.82, 1.18, 0.87), Mat("#", "w"), 1.0),
        Layer(rect(1.02, 0.84, 1.07, 0.95), Mat("|", "d"), 1.0),
        *pine_tree(0.85, 0.97, 0.55, 0.16, 4, NEEDLES, TRUNK),
        *pine_tree(1.38, 0.97, 0.5, 0.18, 4, NEEDLES, TRUNK),
    ]
    return Scene(1.5, parts, span=True)


def synth_floor(hz, vx, part="x", focus=False):
    """A neon grid floor from the horizon down, any width: lines running
    to the vanishing point at vx, and rows that close up towards the
    horizon."""
    out = []
    for k in range(-5, 6):
        out.append(Line([(vx, hz), (vx + k * 0.17, 1.0)], part, focus=focus))
    for z in (1.15, 1.9, 3.4):
        y = hz + (1.0 - hz) / z
        out.append(Line([(-4.0, y), (2.0, y)], part, "=" if z < 1.5 else "-", focus))
    return out


def striped_sun(cx, cy, r, hz):
    sun = circle(cx, cy, r) & rect(-INF, -INF, INF, hz)

    def tone(x, y):
        k = (cy + r - y) / (2 * r)
        gap = math.sin(k * 30) > 1.3 - k * 1.8
        return 0.0 if gap and k < 0.55 else 0.3 + 0.7 * k
    return Layer(sun, Mat(" -=+*#", [(0, "e"), (0.5, "x"), (0.75, "w")], edges=False), tone)


@scene("grid")
def _():
    hz = 0.58
    return Scene(1.5, [
        *scatter(-3.0, 0.0, 1.5, 0.5, 40, ["*", ".", "+", "'"], "t", seed=67),
        striped_sun(1.0, 0.42, 0.3, hz),
        Layer(where(below(lambda x: hz - 0.12 * max(0.0, math.sin(x * 4.0 + 1)) * abs(math.sin(x * 9))),
                    lambda x, y: y < hz), Mat(" .:", [(0, "d"), (0.5, "a")], outline="a"), 0.35,
              focus=False),
        Line([(-4.0, hz), (2.0, hz)], "a", "_", False),
        *synth_floor(hz + 0.01, 1.0),
    ], span=True)


@scene("fire")
def _():
    cx, base = 0.75, 0.82

    def flame(w, h, dx=0.0):
        """A tongue of fire: wide at the base, flickering to a point."""
        def test(x, y):
            t = (base - y) / h                          # 0 at the base, 1 at the tip
            if not 0 <= t <= 1:
                return False
            mid = cx + dx + 0.05 * t * math.sin(t * 7 + dx * 30)
            half = w * (1 - t) ** 0.7 * min(1.0, 0.55 + t * 2) * (1 + 0.3 * math.sin(t * 22 + dx * 40))
            return abs(x - mid) <= half
        return Shape(test, (cx + dx - w * 1.5, base - h, cx + dx + w * 1.5, base))
    logs = [taper([(cx - 0.32, base + 0.1), (cx + 0.3, base - 0.02)], 0.07, 0.06),
            taper([(cx + 0.32, base + 0.1), (cx - 0.3, base - 0.02)], 0.07, 0.06)]
    stones = [ellipse(cx + dx, base + 0.12, 0.06, 0.04) for dx in (-0.45, -0.3, 0.3, 0.45, -0.15, 0.15)]
    return Scene(1.5, [
        Layer(below(lambda x: base + 0.12), Mat(" .,:", "d", edges=False), textured(0.5, 0.4, 30), focus=False),
        Layer(union(*logs), Mat(" :=#", [(0, "d"), (0.5, "x")], outline="x"),
              lambda x, y: 0.4 + 0.5 * (math.sin(x * 120) > 0)),
        Layer(flame(0.2, 0.75), Mat(" .:*#", [(0, "e"), (0.5, "e")], outline="e"), 0.55),
        Layer(flame(0.13, 0.55, 0.02), Mat(" :+*#", [(0, "x"), (0.5, "w")], outline="x"), 0.7),
        Layer(flame(0.06, 0.3, -0.01), Mat(" +*#@", "w", outline="t"), 0.9),
        *[Layer(st, Mat(" .:o@", [(0, "d"), (0.5, "t")], outline="d"), sphere(st.box[0] + 0.06, base + 0.12, 0.06))
          for st in stones],
        *scatter(cx - 0.35, 0.0, cx + 0.35, 0.35, 12, ["*", "'", ".", "`"], "w", seed=71, focus=True),
    ], span=True)


@scene("jellyfish")
def _():
    def jelly(x, y, r, part):
        bell = ellipse(x, y, r, r * 0.8) & rect(-INF, -INF, INF, y + r * 0.1)
        out = [Layer(bell, Mat(" .:-=+*#", [(0, "d"), (0.4, part), (0.85, "t")], outline=part),
                     sphere(x, y - r * 0.1, r, -0.4, -0.8, 0.15, 1.0))]
        for k in range(6):
            tx = x - r * 0.8 + k * r * 0.32
            pts = [(tx + 0.025 * math.sin(j * 1.3 + k), y + r * 0.1 + j * r * 0.28) for j in range(8)]
            out.append(Line(pts, part if k % 2 else "d"))
        return out
    parts = [*[Line([(x, 0.0), (x + 0.15, 0.6)], "d", ".", False) for x in (0.3, 0.6, 0.9, 1.2)]]
    parts += jelly(1.0, 0.25, 0.22, "x")
    parts += jelly(0.5, 0.5, 0.11, "a")
    parts += [Stamp(x, y, "o", "t") for x, y in [(1.35, 0.15), (1.38, 0.08), (0.7, 0.2), (0.25, 0.3)]]
    parts.append(Layer(below(lambda x: 0.9 + 0.04 * math.sin(x * 6)),
                       Mat(" .:,", [(0, "d"), (0.5, "w")], edges=False), textured(0.5, 0.4, 30), focus=False))
    parts += [Line([(x + 0.018 * math.sin(j * 1.4 + x * 9), 0.95 - h * j / 8) for j in range(9)],
                   "g", focus=False, tone=0.5)
              for x, h in ((1.6 - k * 0.13, 0.12 + 0.2 * rand(k, 73)) for k in range(30))]
    return Scene(1.5, parts, span=True)


@scene("terminal")
def _():
    bodies = {26: [("$ minitype --time 30", "g"), ("  loading words... ok", "d"),
                   ("  layout qwerty, 200 words", "d"), ("  ready. type!", "d"), ("", "d"),
                   ("  wpm   112  #########", "t"), ("  acc   98%  ##########", "t"),
                   ("  raw   118  #########.", "t"), ("  cons  91%  #########", "t"), ("", "d"),
                   ("  new personal best!", "w"), ("$ _", "g")],
              20: [("$ minitype --time 30", "g"), ("  loading words... ok", "d"),
                   ("  ready. type!", "d"), ("", "d"),
                   ("  wpm   112  #########", "t"), ("  acc   98%  ##########", "t"),
                   ("  raw   118  #########.", "t"), ("", "d"), ("$ _", "g")],
              14: [("$ minitype --time 30", "g"), ("  wpm   112  ######", "t"),
                   ("  acc   98%  #######", "t"), ("$ _", "g")],
              10: [("$ minitype", "g"), ("$ _", "g")]}
    w = 28

    def term(rows):
        body = bodies[rows]
        top = rows - 2 - (len(body) + 4) - (1 if rows > 10 else 0)
        out = desk(rows)
        out += lines_at(0, top, rows, ["+" + "-" * w + "+", "| o o o" + " " * (w - 14) + "phosphor |",
                                       "+" + "-" * w + "+"], "d")
        out[-2].part = "dde e ed"
        for i, (line, part) in enumerate(body):
            out += lines_at(0, top + 3 + i, rows, ["| " + line.ljust(w - 2) + " |"],
                            ["dd" + part * (w - 2) + "dd"])
            out[-1].tone = 0.85
        out += lines_at(0, top + 3 + len(body), rows, ["+" + "-" * w + "+"], "d")
        return out
    return Scene(lambda rows: (w + 4) / (2 * rows), term, span=True)


@scene("palm")
def _():
    hz = 0.6
    crown = (1.15, 0.22)
    fronds = []
    for tip, droop, w in [((0.85, 0.45), 0.1, 0.07), ((1.45, 0.42), 0.1, 0.07), ((0.9, 0.12), 0.06, 0.06),
                          ((1.42, 0.1), 0.06, 0.06), ((1.15, 0.0), 0.01, 0.05), ((1.05, 0.5), 0.0, 0.05)]:
        fronds.append(frond(crown, tip, droop, w, Mat(" .:;#", [(0, "d"), (0.4, "a")], outline="a"), 0.5))
    return Scene(1.5, [
        *scatter(-3.0, 0.0, 1.5, 0.5, 30, ["*", ".", "+"], "t", seed=79),
        striped_sun(0.75, 0.42, 0.26, hz),
        Line([(-4.0, hz), (2.0, hz)], "e", "_", False),
        *synth_floor(hz + 0.01, 0.75, "e"),
        Layer(taper(bezier((1.25, 0.97), (1.28, 0.6), crown), 0.05, 0.03), Mat("|):(", "d", outline="a"),
              lambda x, y: 0.5 + 0.5 * (math.sin(y * 150) > 0)),
        *fronds,
    ], span=True)


@scene("lollipop")
def _():
    cx, cy, r = 0.8, 0.36, 0.28

    def swirl(x, y):
        dx, dy = x - cx, y - cy
        a = math.atan2(dy, dx)
        d = math.hypot(dx, dy) / r
        return 0.5 + 0.5 * math.sin(a * 2 + d * 14)
    candy = circle(cx, cy, r)

    def build(rows):
        shelf = 1 - 1.5 / rows
        return [
            *desk(rows, "x"),
            *[Stamp(-0.1 - k * 0.42, shelf - 1 / rows, "><(%s)><" % "@*o"[k % 3],
                    "xxx" + "ewg"[k % 3] + "xxx", False, tone=0.6) for k in range(10)],
            Layer(rect(cx - 0.022, cy + r * 0.9, cx + 0.022, shelf), Mat("|#", "t", outline="t"), 0.8),
            Layer(candy, Mat(" .:-=+*#", [(0, "a"), (0.5, "e"), (0.8, "t")], outline="e"), swirl),
            Layer(ellipse(cx - r * 0.45, cy - r * 0.5, r * 0.18, r * 0.08, -35), Mat("o@", "t"), 1.0),
            Layer(poly([(cx - 0.06, cy + r * 0.95), (cx - 0.14, cy + r * 1.25), (cx - 0.02, cy + r * 1.1)])
                  | poly([(cx + 0.06, cy + r * 0.95), (cx + 0.14, cy + r * 1.25), (cx + 0.02, cy + r * 1.1)]),
                  Mat(" :+", "x", outline="x"), 0.7),
            Stamp(0.2, shelf - 1 / rows, "><(@)><", "xxxexxx"),
            Stamp(1.15, shelf - 1 / rows, "><(o)><", "xxxgxxx"),
            Stamp(0.3, 0.2, "><(*)><", "xxxwxxx"),
            *scatter(-3.0, 0.0, 1.4, 0.7, 40, ["*", "+", "."], "w", seed=83),
        ]
    return Scene(1.4, build, span=True)

# ---------------------------------------------------------------- shared backgrounds

def desk(rows, part="x", focus=False, depth=2):
    """A wooden desk top along the bottom `depth` rows, any width."""
    top = (rows - depth + 0.02) / rows

    def grain(x, y):
        return 0.45 + 0.3 * math.sin(x * 9 + 4 * math.sin(y * 40 + x * 2)) \
            + 0.2 * (noise(x * 20, y * 60, 2) - 0.5)
    return [Layer(below(lambda x: top), Mat("_=-~", [(0, "d"), (0.45, part)], edges=False),
                  grain, focus),
            Line([(-4.0, top + 0.3 / rows), (3.0, top + 0.3 / rows)], part, "_", focus, tone=0.9)]


def skyline(base, seed=0, x_max=2.0, part="w"):
    """A city along the bottom, any width, with some windows lit."""
    def top(x):
        i = math.floor((x_max - x) / 0.09)
        return base - 0.06 - 0.22 * rand(i, seed)

    def tone(x, y):
        i, j = math.floor(x / 0.02), math.floor(y / 0.05)
        lit = rand(i * 7 + j * 13, seed + 1) > 0.7
        window = (x / 0.02) % 1 < 0.5 and (y / 0.05) % 1 < 0.5
        return 0.95 if window and lit else 0.4 + 0.15 * (x / 0.09 % 1 < 0.1)
    return Layer(below(top), Mat(" .:#", [(0, "d"), (0.8, part)], edges=False), tone, focus=False)


def rain(n, seed=0, x0=-4.0, x1=1.6, y0=0.25, y1=0.95, part="d"):
    """Slanted streaks of rain, any width."""
    out = []
    for i in range(n):
        x = x0 + (x1 - x0) * rand(i, seed)
        y = y0 + (y1 - y0) * rand(i, seed + 1)
        out.append(Line([(x, y), (x - 0.03, y + 0.05)], part, "/", focus=False, tone=0.35))
    return out


def hills(base, part="g", seed=0, far="d"):
    """Two rows of rolling hills, any width: a dim far one and a near one
    striped like fields."""
    near = lambda x: base + 0.03 * math.sin(x * 3.3 + seed) + 0.02 * math.sin(x * 7.1)
    farther = lambda x: base - 0.07 + 0.05 * math.sin(x * 2.1 + seed + 1)
    return [Layer(below(farther), Mat(" .:", far), 0.5, focus=False),
            Layer(below(near), Mat(" .,;:", [(0, "d"), (0.45, part)]),
                  lambda x, y: 0.5 + 0.3 * math.sin((y - near(x)) * 80 + x * 4), focus=False)]



CODE = "0123456789ABCDEFHJKLPRSTUXZ=+-<>/?#$%"


def ridge(points, jag=0.012, seed=0):
    """The top of a mountain through (x, y) points, rough along the way;
    nothing outside them."""
    def top(x):
        if x < points[0][0] or x > points[-1][0]:
            return INF
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x0 <= x <= x1:
                y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                return y + jag * (math.sin(x * 97 + seed) + 0.6 * math.sin(x * 211 + seed * 2))
        return INF
    return top


@scene("summit")
def _():
    # a sharp peak made of light and code: lit snow gullies on its left
    # face, the shadowed side dissolving into glyphs, a far range behind,
    # a dark ridge in front, pines along the bottom, and a sky of digits
    peak = ridge([(0.22, 0.8), (0.42, 0.5), (0.52, 0.36), (0.6, 0.41), (0.72, 0.26), (0.84, 0.14),
                  (0.95, 0.04), (1.02, 0.1), (1.1, 0.17), (1.2, 0.29), (1.32, 0.33), (1.42, 0.42),
                  (1.58, 0.56)], 0.01, 1)

    def spine(y):
        return 0.95 - (y - 0.04) * 0.42                     # the sunlit edge runs down-left

    def peak_tone(x, y):
        lit = x < spine(y)
        snow = max(0.0, 1 - (y - 0.04) * 1.35)              # more snow higher up
        if lit:
            gully = math.sin((x * 9 + y * 15) * 7 + 2 * math.sin(y * 20))
            t = 0.55 + 0.45 * snow + 0.22 * gully
        else:
            gully = math.sin((-x * 10 + y * 13) * 7 + 2 * math.sin(x * 15))
            t = 0.24 + 0.7 * snow * max(0.0, gully) ** 2
        return max(0.0, min(1.0, t + 0.12 * (noise(x * 40, y * 40, 4) - 0.5)))

    far = ridge([(-4.0, 0.5)] + [(-3.9 + k * 0.18, 0.42 + 0.12 * rand(k, 41)) for k in range(31)]
                + [(1.8, 0.5)], 0.008, 2)

    def far_tone(x, y):
        return max(0.0, 0.5 - (y - far(x)) * 2.2 + 0.25 * math.sin((x * 12 + y * 18) * 5))

    front = ridge([(-4.0, 0.66), (-2.6, 0.6), (-1.5, 0.66), (-0.6, 0.58), (0.05, 0.6), (0.3, 0.55),
                   (0.5, 0.64), (0.75, 0.72), (1.0, 0.76), (1.3, 0.72), (1.8, 0.68)], 0.012, 3)

    def front_tone(x, y):
        # snow caught in gullies running down to the left, fading lower down
        streak = math.sin((x * 3 + y * 7) * 9 + 1.5 * math.sin(x * 4))
        depth = y - front(x)
        snow = max(0.0, 1 - depth / 0.16)
        mist = min(0.4, max(0.0, depth - 0.08) * 2.5)        # the valley fills with mist
        return 0.24 + mist + (0.45 * snow if streak > 0.55 else 0.0)

    sky = rect(-4.5, -0.5, 2.0, 1.5)
    rock = Mat(" .:-=+*#%@", [(0, "d"), (0.4, "g"), (0.75, "t")], outline="t")
    return Scene(1.55, [
        Layer(sky, Mat("0", "d", edges=False, code=CODE, code_below=2.0, seed=1),
              lambda x, y: 0.08 + 0.35 * noise(x * 9, y * 14, 6) ** 2, focus=False),
        Layer(below(far), Mat(" .:-=+*#", [(0, "d"), (0.45, "g")], outline="g"),
              lambda x, y: max(0.24, far_tone(x, y)), focus=False),
        Layer(below(peak), rock, peak_tone),
        Layer(below(front), Mat(" .:-=+#%@", [(0, "d"), (0.5, "t")], outline="g"),
              front_tone, focus=False),
        Layer(where(below(treeline(0.95, 0.24, 0.032, 11)), lambda x, y: y < 0.9),
              Mat("#", "d", outline="g"), lambda x, y: 0.1 + 0.15 * noise(x * 30, y * 30, 12),
              focus=False),
        Layer(below(lambda x: 0.9), Mat("0", "d", edges=False, code=CODE, code_below=2.0, seed=4),
              lambda x, y: 0.15 + 0.4 * noise(x * 11, y * 20, 9), focus=False),
    ], span=True, sizes=(32, 26, 20, 14, 10))


SCENES.update((name, make()) for name, make in _MAKERS.items())
