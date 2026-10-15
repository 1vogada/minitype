"""The whole main-menu screen, as the app writes it, to a PNG.

    python screen_png.py OUT.png W H theme [key=value ...]

key=value sets a Settings field (art_behind=1, art_style=upscaled, ...).
Parses the app's real escape codes; block glyphs are drawn exactly,
letters as blobs. env SCALE=1, MT_ROOT.
"""
import os
import re
import sys
import tempfile
from unittest import mock

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apppng                                            # noqa: E402  (puts the checkout on the path)
from minitype.terminal import console, keys              # noqa: E402
from minitype.context import App                         # noqa: E402
from minitype.ui import main_menu as mm                  # noqa: E402

TOKEN = re.compile(r"\x1b\[([0-9;?]*)([A-Za-z])|\x1b\][^\x07]*\x07|(.)", re.S)
DEFAULT_FG, DEFAULT_BG = (204, 204, 204), (12, 12, 12)


def frame(w, h, theme, settings):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    a = App()
    a.settings.theme = theme
    for k, v in settings.items():
        old = getattr(a.settings, k)
        if isinstance(old, bool):
            v = v in ("1", "true", "on")
        elif isinstance(old, int):
            v = int(v)
        setattr(a.settings, k, v)
    a.styles()
    out = []
    seq = iter([keys.ESC] * 4 + ["q"] * 2)
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        try:
            mm.main_menu(a)
        except (StopIteration, SystemExit):
            pass
    return [o for o in out if o.startswith("\x1b[H")][0]


def cells(raw, w, h):
    rows, fg, bg, rev = [], None, None, False
    for line in raw.split("\n")[:h]:
        row = []
        for m in TOKEN.finditer(line):
            params, cmd, ch = m.group(1), m.group(2), m.group(3)
            if ch is not None:
                f, b = (fg or DEFAULT_FG), (bg or DEFAULT_BG)
                row.append((ch, b, f) if rev else (ch, f, b))
                continue
            if cmd != "m":
                continue
            nums = [int(x) if x else 0 for x in (params or "0").split(";")]
            i = 0
            while i < len(nums):
                n = nums[i]
                if n == 0:
                    fg = bg = None
                    rev = False
                elif n == 7:
                    rev = True
                elif n in (38, 48) and i + 1 < len(nums) and nums[i + 1] == 2:
                    c = tuple(nums[i + 2:i + 5])
                    if n == 38:
                        fg = c
                    else:
                        bg = c
                    i += 4
                elif n in (38, 48) and i + 1 < len(nums) and nums[i + 1] == 5:
                    i += 2
                elif n == 39:
                    fg = None
                elif n == 49:
                    bg = None
                i += 1
        # the line clear after a row fills the rest with the current background
        row += [(" ", DEFAULT_FG, bg or DEFAULT_BG)] * (w - len(row))
        rows.append(row[:w])
    return rows


if __name__ == "__main__":
    out, w, h, theme = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    settings = dict(a.split("=", 1) for a in sys.argv[5:])
    rows = cells(frame(w, h, theme, settings), w, h)
    apppng.draw([(rows, DEFAULT_BG)], out)
