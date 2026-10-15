"""Render pictures exactly as the app stores and paints them, to one PNG.

    python apppng.py OUT.png theme:style[:size] [theme:style[:size] ...]

style: revamp | upscaled | blocks | combined.  size: index into the
picture's sizes (0 = biggest).  env SCALE=2.  Colours come from the
Picture's own escape codes, so this is what the terminal receives.
Letters are drawn as soft blobs.
"""
import os
import re
import struct
import sys
import tempfile
import zlib

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
ROOT = os.environ.get("MT_ROOT", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))   # this checkout unless told otherwise
sys.path[:0] = [ROOT, os.path.join(ROOT, "tools")]
from minitype.terminal import art, style          # noqa: E402

SCALE = int(os.environ.get("SCALE", "2"))
GW, GH = 4, 8
Q = {"▘": "1000", "▝": "0100", "▖": "0010", "▗": "0001", "▚": "1001", "▞": "0110",
     "▙": "1011", "▛": "1110", "▜": "1101", "▟": "0111", "▀": "1100", "▄": "0011",
     "▌": "1010", "▐": "0101", "█": "1111"}
_C = re.compile(r"\x1b\[(38|48);2;(\d+);(\d+);(\d+)m")


def cover(ch):
    g = [0.0] * (GW * GH)

    def fill(x0, y0, x1, y1, v=1.0):
        for y in range(y0, y1):
            for x in range(x0, x1):
                g[y * GW + x] = v
    if ch in Q:
        for k, (x0, y0) in enumerate(((0, 0), (2, 0), (0, 4), (2, 4))):
            if Q[ch][k] == "1":
                fill(x0, y0, x0 + 2, y0 + 4)
    elif ch in "▁▂▃▅▆▇":
        fill(0, GH - ("▁▂▃▄▅▆▇".index(ch) + 1), GW, GH)
    elif ch == "▔":
        fill(0, 0, GW, 1)
    elif ch in "▏▎▍▋▊▉":
        fill(0, 0, {"▏": 1, "▎": 1, "▍": 2, "▋": 3, "▊": 3, "▉": 4}[ch], GH)
    elif ch == "▕":
        fill(GW - 1, 0, GW, GH)
    elif ch in "░▒▓":
        fill(0, 0, GW, GH, {"░": 0.25, "▒": 0.5, "▓": 0.75}[ch])
    elif 0x2800 <= ord(ch) <= 0x28FF:
        bits = ord(ch) - 0x2800
        pos = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]
        for b, (cx, ry) in enumerate(pos):
            if bits >> b & 1:
                fill(cx * 2, ry * 2, cx * 2 + 1, ry * 2 + 1)
    elif ch != " ":
        fill(1, 2, 3, 6, 0.6)
    return g


def picture(theme, sty, size):
    st = style.Styles(theme)
    pal = st.art_palette(True)
    ground = style.rgb_of_code(st.background, 48) or (18, 18, 22)
    name = art.THEME_ART[theme]
    pieces = art.resolve(name, sty)
    pic = art.paint(pieces[size], pal)
    rows = []
    for r, line in enumerate(pic.lines):
        cells = []
        for c, ch in enumerate(line):
            fg = bg = None
            for kind, *v in _C.findall(pic._codes[r][c]):
                if kind == "38":
                    fg = tuple(map(int, v))
                else:
                    bg = tuple(map(int, v))
            cells.append((ch, fg, bg))
        rows.append(cells)
    return rows, ground


def png(path, w, h, img):
    raw = b"".join(b"\x00" + bytes(r) for r in img)

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def draw(pics, out, gap=8):
    cw, chh = GW * SCALE, GH * SCALE
    W = max(max(len(r) for r in p) for p, _ in pics) * cw
    H = sum(len(p) * chh + gap for p, _ in pics)
    img = [bytearray(b"\x10\x10\x10" * W) for _ in range(H)]
    y0 = 0
    for rows, ground in pics:
        width = max(len(r) for r in rows)
        for r, cells in enumerate(rows):
            cells = cells + [(" ", None, None)] * (width - len(cells))
            for c, (ch, fg, bg) in enumerate(cells):
                b = bg or ground
                f = fg or b
                g = cover(ch)
                for gy in range(GH):
                    for gx in range(GW):
                        v = g[gy * GW + gx]
                        col = bytes(int(b[k] + (f[k] - b[k]) * v) for k in range(3))
                        for sy in range(SCALE):
                            row = img[y0 + r * chh + gy * SCALE + sy]
                            px = (c * cw + gx * SCALE) * 3
                            row[px:px + 3 * SCALE] = col * SCALE
        y0 += len(rows) * chh + gap
    png(out, W, H, img)
    print("wrote", out, W, "x", H)


if __name__ == "__main__":
    pics = []
    for spec in sys.argv[2:]:
        theme, sty, *rest = spec.split(":")
        rows, ground = picture(theme, sty, int(rest[0]) if rest else 0)
        print(spec, len(rows), "rows x", max(len(r) for r in rows), "cols")
        pics.append((rows, ground))
    draw(pics, sys.argv[1])
