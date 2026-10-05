"""Console output: ANSI setup, screen and cursor control, and drawing whole
frames clipped to whatever size the terminal currently is."""

import ctypes
import os
import re
import shutil
import sys

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")
RESET = "\x1b[0m"
MIN_W, MIN_H = 20, 5

_last_size = None
_background = ""

# corner, corner, corner, corner, across, down. The sides are as wide as
# "down": "thick" has two-column sides, which look as thick as its one-row
# top and bottom since a terminal cell is about twice as tall as it's wide
BLOCK = "█"
BORDERS = {
    "ascii": ("+", "+", "+", "+", "-", "|"),
    "line": ("┌", "┐", "└", "┘", "─", "│"),
    "rounded": ("╭", "╮", "╰", "╯", "─", "│"),
    "double": ("╔", "╗", "╚", "╝", "═", "║"),
    "heavy": ("┏", "┓", "┗", "┛", "━", "┃"),
    "block": (BLOCK,) * 6,
    "thick": (BLOCK * 2, BLOCK * 2, BLOCK * 2, BLOCK * 2, BLOCK, BLOCK * 2),
}
# the theme's frame and corner art, set by set_decor()
_decor = {"border": None, "border_style": "", "art": None, "art_scope": "menus"}


def enable_vt():
    """Turn on ANSI escape processing in the Windows console. Terminals on
    Linux and macOS understand ANSI already."""
    if os.name != "nt":
        return
    k = ctypes.windll.kernel32
    h = k.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if k.GetConsoleMode(h, ctypes.byref(mode)):
        k.SetConsoleMode(h, mode.value | 0x0004)


def setup():
    enable_vt()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def write(s):
    sys.stdout.write(s)


def flush():
    sys.stdout.flush()


def set_title(text):
    write(f"\x1b]0;{text}\x07")


def cursor(show):
    write("\x1b[?25h" if show else "\x1b[?25l")


def clear():
    write(RESET + "\x1b[2J\x1b[H")


def bell():
    write("\a")


def term_size():
    """The terminal's real (columns, rows), never below the minimum."""
    s = shutil.get_terminal_size((80, 24))
    return max(MIN_W, s.columns), max(MIN_H, s.lines)


def size():
    """(columns, rows) that screens can lay text out in: the terminal, or
    the inside of the border when there is one."""
    w, h = term_size()
    if _decor["border"]:
        side = len(_decor["border"][5])
        return max(MIN_W, w - 2 * side), max(MIN_H, h - 2)
    return w, h


def width():
    """Usable width for the word display."""
    return max(10, size()[0] - 4)


def visible_len(s):
    return len(ANSI.sub("", s))


def clip(s, w):
    """Cut s to w visible characters, keeping escape codes intact."""
    out, n, i = [], 0, 0
    while i < len(s):
        m = ANSI.match(s, i)
        if m:
            out.append(m.group())
            i = m.end()
            continue
        if n >= w:
            break
        out.append(s[i])
        n += 1
        i += 1
    return "".join(out)


def pad(s, w):
    """Clip or space-pad s to exactly w visible characters."""
    s = clip(s, w)
    return s + RESET + " " * (w - visible_len(s))


def present(lines, focus=None, pinned=(), scene="menu"):
    """Draw a whole frame in place. Lines are clipped to the width there
    is; if there are more than fit, the view scrolls to keep line `focus`
    on screen. `pinned` lines stick to the bottom when there's room for
    them. A resize clears the screen first so no old content is left
    behind.

    The theme's decorations go on here: the corner art (on menus, or on
    every `scene` if the art setting says so) and the border around it all."""
    global _last_size
    term = term_size()
    if term != _last_size:
        write("\x1b[2J")
        _last_size = term
    w, h = size()
    pinned = list(pinned) if len(pinned) < h - 2 else []
    body_h = h - len(pinned)
    lines = list(lines)
    top = 0
    if len(lines) > body_h:
        f = focus if focus is not None else 0
        top = max(0, min(f - body_h // 2, len(lines) - body_h))
    view = lines[top:top + body_h]
    d = _decor
    art = d["art"] if d["art"] and (d["art_scope"] == "everywhere"
                                    or scene == "menu") else None
    if pinned or art or d["border"]:
        view += [""] * (body_h - len(view))     # full height: pinned / art / frame
    view += pinned
    rows = [clip(line, w - 1) for line in view]
    if art:
        rows = overlay_art(rows, art, w - 1, len(pinned))
    if d["border"]:
        rows = frame(rows, d["border"], d["border_style"], w - 1)
    bg = _background
    # with a theme background, every reset puts the background straight
    # back, and the line ends (and the rest of the screen) are cleared
    # while it's active, which fills them with it
    out = "\x1b[K\n".join(bg + row.replace(RESET, RESET + bg) + RESET + bg
                          for row in rows)
    write("\x1b[H" + out + "\x1b[K\x1b[J" + (RESET if bg else ""))
    flush()


def overlay_art(rows, versions, width, pinned_n):
    """Put the art in the bottom-right corner, above any pinned lines with
    a row to spare. `versions` are the picture's sizes, biggest first (art
    Pictures); the first whose focus fits without touching any text, in
    the right two-thirds of the screen, is drawn. A spanning picture loses
    what doesn't fit on its left, and the background part of a row steps
    back from text rather than cover it. If none fits the frame is left
    without art."""
    bottom = len(rows) - pinned_n - (2 if pinned_n else 1)
    avail = width - 1
    for pic in versions:
        w = min(pic.width, avail) if pic.span else pic.width
        skip = pic.width - w                 # columns cut off the left
        top, col = bottom - pic.height + 1, avail - w
        if top < 1 or col < 0:
            continue
        ends = [visible_len(rows[top + k]) for k in range(pic.height)]
        starts = [col + pic.keep[k] - skip for k in range(pic.height)
                  if pic.keep[k] < pic.width]
        if not starts or min(starts) < width // 3 or any(
                pic.keep[k] < pic.width and col + pic.keep[k] - skip < ends[k] + 2
                for k in range(pic.height)):
            continue
        # the background only runs the full width below the last text;
        # beside text it keeps to the picture's own box
        box = min(starts) - col
        last_text = max((k for k in range(pic.height) if ends[k]), default=-1)
        rows = list(rows)
        for k in range(pic.height):
            start = max(0, ends[k] + 2 - col, box if k <= last_text else 0)
            if start >= w:
                continue
            r = rows[top + k]
            rows[top + k] = (r + RESET + " " * (col + start - ends[k])
                             + pic.row(k, skip + start))
        return rows
    return rows


def frame(rows, chars, style, inner):
    """A border around the rows, `inner` columns wide inside; the sides are
    as wide as the side character. It stops a column short of the
    terminal's edge: writing the very last column leaves some terminals
    waiting to wrap, and the line clear after it would then wipe the
    corner."""
    tl, tr, bl, br, across, down = chars
    side = style + down + RESET
    return ([style + tl + across * inner + tr + RESET]
            + [side + pad(r, inner) + side for r in rows]
            + [style + bl + across * inner + br + RESET])


def set_decor(border=None, border_style="", art=None, art_scope="menus"):
    """The theme's frame and corner art for present(): border is a BORDERS
    key or None; art the picture's sizes, biggest first, each a list of
    Pictures (see art.py), or None; art_scope "menus" or "everywhere"."""
    _decor.update(border=BORDERS.get(border), border_style=border_style,
                  art=art or None, art_scope=art_scope)


def set_background(code):
    """The theme's background escape code, "" for the terminal's own.
    present() paints every frame with it."""
    global _background
    _background = code


def bail():
    """Panic exit: wipe the screen and drop out, leaving no scrollback."""
    clear()
    cursor(True)
    flush()
    raise SystemExit
