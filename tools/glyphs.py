"""Where each character's ink sits in its cell, measured from a real
terminal font, for picking characters by shape (tools/artgen.py).

ASCII art looks best when a character is chosen for its shape, not just
how dark it is: "_" for an edge along the bottom of a cell, "'" for a
speck at the top, "d" for a shape filling the lower right. This reads a
TrueType font (glyf outlines, no libraries), draws every character into
its terminal cell and records the coverage of a grid of COLS x ROWS
patches, 0 (no ink) to 1 (full).

    python tools/glyphs.py [font.ttf]     rebuild tools/glyph_shapes.json

The result is saved with the tools so building the art needs no font.
"""

import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "glyph_shapes.json")
COLS, ROWS = 4, 8              # patches per cell
FONTS = [r"C:\Windows\Fonts\CascadiaMono.ttf", r"C:\Windows\Fonts\consola.ttf"]
# printable ASCII, plus a few Latin-1 marks that look like it and fill gaps
# in it: a line along the top (macron), a dot in the middle, a degree ring
CHARSET = "".join(chr(c) for c in range(33, 127)) + "¯·°´¸¨¦×"


class Font:
    def __init__(self, path):
        self.data = data = open(path, "rb").read()
        n = struct.unpack(">H", data[4:6])[0]
        self.tables = {}
        for i in range(n):
            tag, _, off, ln = struct.unpack(">4sIII", data[12 + 16 * i:28 + 16 * i])
            self.tables[tag.decode("latin-1")] = (off, ln)
        head = self.tables["head"][0]
        self.upem = struct.unpack(">H", data[head + 18:head + 20])[0]
        self.long_loca = struct.unpack(">h", data[head + 50:head + 52])[0] == 1
        hhea = self.tables["hhea"][0]
        self.ascent, self.descent, self.gap = struct.unpack(">hhh", data[hhea + 4:hhea + 10])
        self.n_hmetrics = struct.unpack(">H", data[hhea + 34:hhea + 36])[0]
        self.cmap = self._cmap()

    def _cmap(self):
        d = self.data
        base = self.tables["cmap"][0]
        n = struct.unpack(">H", d[base + 2:base + 4])[0]
        for i in range(n):
            pid, eid, off = struct.unpack(">HHI", d[base + 4 + 8 * i:base + 12 + 8 * i])
            sub = base + off
            if struct.unpack(">H", d[sub:sub + 2])[0] == 4 and pid in (0, 3):
                segx2 = struct.unpack(">H", d[sub + 6:sub + 8])[0]
                seg = segx2 // 2
                ends = struct.unpack(f">{seg}H", d[sub + 14:sub + 14 + segx2])
                starts = struct.unpack(f">{seg}H", d[sub + 16 + segx2:sub + 16 + 2 * segx2])
                deltas = struct.unpack(f">{seg}h", d[sub + 16 + 2 * segx2:sub + 16 + 3 * segx2])
                ro_at = sub + 16 + 3 * segx2
                ros = struct.unpack(f">{seg}H", d[ro_at:ro_at + segx2])
                out = {}
                for k in range(seg):
                    for c in range(starts[k], ends[k] + 1):
                        if c == 0xFFFF:
                            continue
                        if ros[k] == 0:
                            g = (c + deltas[k]) & 0xFFFF
                        else:
                            at = ro_at + 2 * k + ros[k] + 2 * (c - starts[k])
                            g = struct.unpack(">H", d[at:at + 2])[0]
                            if g:
                                g = (g + deltas[k]) & 0xFFFF
                        out[c] = g
                return out
        raise ValueError("no unicode cmap")

    def advance(self, g):
        hmtx = self.tables["hmtx"][0]
        g = min(g, self.n_hmetrics - 1)
        return struct.unpack(">H", self.data[hmtx + 4 * g:hmtx + 4 * g + 2])[0]

    def _glyph_at(self, g):
        loca = self.tables["loca"][0]
        d = self.data
        if self.long_loca:
            a, b = struct.unpack(">II", d[loca + 4 * g:loca + 4 * g + 8])
        else:
            a, b = (2 * v for v in struct.unpack(">HH", d[loca + 2 * g:loca + 2 * g + 4]))
        return (self.tables["glyf"][0] + a, b - a)

    def contours(self, g):
        """The glyph's outline as closed polylines (quadratic curves
        flattened), in font units."""
        at, ln = self._glyph_at(g)
        if ln == 0:
            return []
        d = self.data
        nc = struct.unpack(">h", d[at:at + 2])[0]
        if nc < 0:                                 # composite: its parts, moved
            out, p = [], at + 10
            while True:
                flags, sub = struct.unpack(">HH", d[p:p + 4])
                p += 4
                if flags & 1:
                    dx, dy = struct.unpack(">hh", d[p:p + 4])
                    p += 4
                else:
                    dx, dy = struct.unpack(">bb", d[p:p + 2])
                    p += 2
                sx = sy = 1.0
                if flags & 8:
                    sx = sy = struct.unpack(">h", d[p:p + 2])[0] / 16384
                    p += 2
                elif flags & 0x40:
                    sx, sy = (v / 16384 for v in struct.unpack(">hh", d[p:p + 4]))
                    p += 4
                elif flags & 0x80:
                    a, _, _, b = (v / 16384 for v in struct.unpack(">hhhh", d[p:p + 8]))
                    sx, sy = a, b
                    p += 8
                for c in self.contours(sub):
                    out.append([(x * sx + dx, y * sy + dy) for x, y in c])
                if not flags & 0x20:
                    return out
        ends = struct.unpack(f">{nc}H", d[at + 10:at + 10 + 2 * nc])
        npts = ends[-1] + 1
        p = at + 10 + 2 * nc
        ilen = struct.unpack(">H", d[p:p + 2])[0]
        p += 2 + ilen
        flags = []
        while len(flags) < npts:
            f = d[p]
            p += 1
            flags.append(f)
            if f & 8:
                flags += [f] * d[p]
                p += 1
        coords = []
        for short, same in ((2, 16), (4, 32)):
            v, vals = 0, []
            for f in flags:
                if f & short:
                    delta = d[p]
                    p += 1
                    v += delta if f & same else -delta
                elif not f & same:
                    v += struct.unpack(">h", d[p:p + 2])[0]
                    p += 2
                vals.append(v)
            coords.append(vals)
        pts = list(zip(coords[0], coords[1], [f & 1 for f in flags]))
        out, start = [], 0
        for e in ends:
            out.append(_flatten(pts[start:e + 1]))
            start = e + 1
        return out


def _flatten(pts):
    """A contour of on/off-curve points as a polyline."""
    if not pts:
        return []
    # start on an on-curve point (or the midpoint of two off-curve ones)
    if not pts[0][2]:
        if pts[-1][2]:
            pts = [pts[-1]] + pts[:-1]
        else:
            mid = ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2, 1)
            pts = [mid] + pts
    out = [(pts[0][0], pts[0][1])]
    n = len(pts)
    i = 1
    cur = pts[0]
    while i <= n:
        p = pts[i % n]
        if p[2]:
            out.append((p[0], p[1]))
            cur = p
            i += 1
            continue
        nxt = pts[(i + 1) % n]
        end = nxt if nxt[2] else ((p[0] + nxt[0]) / 2, (p[1] + nxt[1]) / 2, 1)
        for k in range(1, 9):
            t = k / 8
            x = (1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * p[0] + t * t * end[0]
            y = (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * p[1] + t * t * end[1]
            out.append((x, y))
        cur = end
        i += 1 if not nxt[2] else 2
    return out


def coverage(font, ch, cols=COLS, rows=ROWS, sub=6):
    """How much ink each of cols x rows patches of the character's cell
    holds, 0..1, top row first."""
    g = font.cmap.get(ord(ch))
    if g is None:
        return None
    polys = font.contours(g)
    width = font.advance(g)
    top, bottom = font.ascent, font.descent          # descent is negative
    height = top - bottom
    gw, gh = cols * sub, rows * sub
    grid = []
    for j in range(gh):
        y = top - (j + 0.5) * height / gh
        xs = []                                    # crossings with their winding
        for poly in polys:
            for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append((x0 + (y - y0) * (x1 - x0) / (y1 - y0), 1 if y1 > y0 else -1))
        xs.sort()
        row = []
        for i in range(gw):
            x = (i + 0.5) * width / gw
            wind = sum(w for cx, w in xs if cx < x)
            row.append(1 if wind != 0 else 0)
        grid.append(row)
    return [[sum(grid[r * sub + a][c * sub + b] for a in range(sub) for b in range(sub)) / sub / sub
             for c in range(cols)] for r in range(rows)]


def build(path=None):
    path = path or next(p for p in FONTS if os.path.exists(p))
    font = Font(path)
    shapes = {}
    for ch in CHARSET:
        cov = coverage(font, ch)
        if cov is not None:
            shapes[ch] = cov
    shapes[" "] = [[0.0] * COLS for _ in range(ROWS)]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"font": os.path.basename(path), "cols": COLS, "rows": ROWS,
                   "shapes": shapes}, f, ensure_ascii=False, separators=(",", ":"))
    return shapes


def load():
    with open(OUT, encoding="utf-8") as f:
        return json.load(f)["shapes"]


if __name__ == "__main__":
    shapes = build(sys.argv[1] if len(sys.argv) > 1 else None)
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    for ch in "_-'.,dbPY/\\|o#@¯":
        print(repr(ch))
        for row in shapes[ch]:
            print("  " + "".join(" .:-=+*#%@"[min(9, int(v * 10))] for v in row))
    print(len(shapes), "characters")
