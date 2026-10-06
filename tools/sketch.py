"""Line-art drafts for tools/revamp_art.py: lay out arcs and strokes in
character cells and get them back as stepped ASCII (_,.-'"^ / | \\),
ready to finish by hand.

    from sketch import arc, line, draft
    print(draft(16, 50, [arc(22, 7.5, 14, 7, -60, 240), line((1, 1), (5, 3))]))

Coordinates are (column, row) from the top left; an arc's radii are in
columns and rows (2:1 looks round), its angles in degrees, 0 to the
right and growing clockwise on screen.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import artgen            # noqa: E402
import artgen_ascii      # noqa: E402


def arc(cx, cy, rx, ry, a0, a1, n=None):
    """Points along an ellipse arc, in cells."""
    n = n or max(8, int(abs(a1 - a0) / 4))
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def curve(p0, p1, p2, n=24):
    """A quadratic curve through control point p1, in cells."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (k / n for k in range(n + 1))]


def line(*pts):
    return list(pts)


def draft(rows, cols, paths):
    """The paths drawn as ASCII lines in a rows x cols box."""
    def scene(p):
        return [(x / (2 * rows), (y + 0.5) / rows) for x, y in p]
    items = [artgen.Line(scene(p), "a") for p in paths]
    sc = artgen.Scene(cols / (2 * rows), items)
    chars = artgen_ascii.render(sc, rows, raw=True)[0]
    return "\n".join("".join(r).rstrip() for r in chars)


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    print(draft(16, 44, [arc(22, 7.5, 14, 7, -62, 242), arc(28, 6.6, 12, 6.2, -96, 228)]))
