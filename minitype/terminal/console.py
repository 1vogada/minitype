"""Console output: ANSI setup, screen and cursor control, and drawing whole
frames clipped to whatever size the terminal currently is."""

import ctypes
import os
import re
import shutil
import sys
from functools import lru_cache

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")
RESET = "\x1b[0m"
# put in a line, it marks the rest of the line as floating: text that may
# go over the corner art (a menu's help box) and so doesn't push the art
# smaller. It takes no room, and present() takes it out before drawing
FLOAT = "\x1b]minitype-float\x07"
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
_decor = {"border": None, "border_style": "", "art": None, "art_scope": "menus",
          "behind": False, "panel": False, "shadow": "", "fade": None}
_last_frame = []        # the last present()'s arguments, for repaint()
_overlay = []           # lines of a box drawn over the middle of every frame (a dialog)


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
    _last_frame[:] = [lines, focus, pinned, scene]
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
    art = d["art"] if art_shown(scene) else None
    if pinned or art or d["border"]:
        view += [""] * (body_h - len(view))     # full height: pinned / art / frame
    view += pinned
    rows = [clip(line, w - 1) for line in view]
    if art and d["panel"]:
        # the art full size over the whole screen, the text in a panel of
        # its own on top of it, the key hints in another along the bottom
        body, hints = rows[:body_h], [r for r in rows[body_h:] if visible_len(r)]
        art_rows = overlay_art([""] * len(rows), art, w - 1, 0, True)
        rows = _panel(art_rows, body, w - 1, 0)
        if hints:
            rows = _panel(rows, hints, w - 1, len(rows) - len(hints) - 2)
    elif art:
        rows = overlay_art(rows, art, w - 1, len(pinned), d["behind"])
    if d["border"]:
        rows = frame(rows, d["border"], d["border_style"], w - 1)
    if _overlay:
        rows = _over(rows, _overlay)
    bg = _background
    # with a theme background, every reset puts the background straight
    # back, and the line ends (and the rest of the screen) are cleared
    # while it's active, which fills them with it
    out = "\x1b[K\n".join(bg + row.replace(FLOAT, "").replace(RESET, RESET + bg)
                          + RESET + bg for row in rows)
    write("\x1b[H" + out + "\x1b[K\x1b[J" + (RESET if bg else ""))
    flush()


def panel_shown(scene="menu"):
    """Whether present() puts the text in a panel over the art."""
    return _decor["panel"] and art_shown(scene)


def art_shown(scene="menu"):
    """Whether present() puts the corner art on a frame of this scene."""
    d = _decor
    return bool(d["art"]) and (d["art_scope"] == "everywhere" or scene == "menu")


def _text_ends(row):
    """Where the row's fixed text ends and where all of it ends. They
    differ when the row has floating text (see FLOAT), which the art is
    placed without."""
    full = visible_len(row)
    i = row.find(FLOAT)
    if i < 0:
        return full, full
    return len(ANSI.sub("", row[:i]).rstrip()), full


def _cells(s):
    """The visible characters of s, each with the codes in force for it."""
    out, codes, i = [], "", 0
    while i < len(s):
        m = ANSI.match(s, i)
        if m:
            c = m.group()
            if c == RESET:
                codes = ""
            elif c.endswith("m"):
                codes += c
            i = m.end()
            continue
        out.append((codes, s[i]))
        i += 1
    return out


@lru_cache(maxsize=256)
def _art_cells(pic, k, start, col):
    """Row k of a picture as cells, from its column `start`, placed at
    column col. The art doesn't change between frames, so it's kept."""
    return tuple([("", " ")] * col + _cells(pic.row(k, start)))


def _behind(cell):
    """The background a letter takes over this art cell: the art's own
    background, or a full block's colour; "" over blank art."""
    codes, ch = cell
    m = re.findall(r"\x1b\[48;[0-9;]*m", codes)
    if m:
        return m[-1]
    if ch in "█▓":
        m = re.findall(r"\x1b\[38;([0-9;]*)m", codes)
        if m:
            return "\x1b[48;" + m[-1] + "m"
    return ""


def _layer(row, pic, card):
    """The row drawn over a row of the art (cells from _art_cells). The art
    shows through wherever the row has a plain blank; letters, and blanks
    with a highlight or background of their own, cover it. `card` is the
    (from, to) columns of floating text (a help box), which covers the art
    whole."""
    text = _cells(row)
    out, cur = [], None
    for x in range(max(len(text), len(pic))):
        t = text[x] if x < len(text) else ("", " ")
        a = pic[x] if x < len(pic) else ("", " ")
        solid = (t[1] != " " or "\x1b[7m" in t[0] or "\x1b[48;" in t[0]
                 or card[0] <= x < card[1])
        codes, ch = t if solid or (a[1] == " " and not a[0]) else a
        if solid and t[1] != " " and not card[0] <= x < card[1] and "\x1b[48;" not in t[0] \
                and "\x1b[7m" not in t[0]:
            codes = t[0] + _behind(a)         # printed on the art, not punched out of it
        if codes != cur:
            out.append(RESET + codes)
            cur = codes
        out.append(ch)
    return "".join(out).rstrip() + RESET


def overlay_art(rows, versions, width, pinned_n, behind=False):
    """Put the art in the bottom-right corner, above any pinned lines with
    a row to spare. `versions` are the picture's sizes, biggest first (art
    Pictures); the first whose focus fits without touching any text, in
    the right two-thirds of the screen, is drawn. A spanning picture loses
    what doesn't fit on its left, and the background part of a row steps
    back from text rather than cover it. If none fits the frame is left
    without art. Floating text doesn't count when fitting it: it stays
    on top, and the art shows again after it.

    With `behind`, the biggest picture that fits the screen is drawn
    whatever text there is, behind it: the text goes over the art letter
    by letter, and only floating text gets a solid card."""
    bottom = len(rows) - pinned_n - (2 if pinned_n else 1)
    avail = width - 1
    # on a screen wider than a spanning picture, its scenery grows to fill it
    versions = [pic.wider(avail) for pic in versions]
    fade = _decor.get("fade")
    if fade and fade[0] != "off":
        # pictures with backgrounds dissolve into the screen at their edges
        versions = [pic.faded(*fade) if getattr(pic, "back", False) else pic for pic in versions]
    if behind:
        for pic in versions:
            w = min(pic.width, avail) if pic.span else pic.width
            top, col = bottom - pic.height + 1, avail - w
            if top < 1 or col < 0:
                continue
            rows = list(rows)
            for k in range(pic.height):
                r = rows[top + k]
                i = r.find(FLOAT)
                card = (visible_len(r[:i]), visible_len(r)) if i >= 0 else (0, 0)
                rows[top + k] = _layer(r, _art_cells(pic, k, pic.width - w, col), card)
            return rows
        return rows
    for pic in versions:
        w = min(pic.width, avail) if pic.span else pic.width
        skip = pic.width - w                 # columns cut off the left
        top, col = bottom - pic.height + 1, avail - w
        if top < 1 or col < 0:
            continue
        spans = [_text_ends(rows[top + k]) for k in range(pic.height)]
        ends = [solid for solid, _ in spans]
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
            solid, full = spans[k]
            start = max(0, solid + 2 - col, box if k <= last_text else 0)
            if full > solid:             # floating text: the art goes on after it
                start = max(start, full + 1 - col)
            if start >= w:
                continue
            r = rows[top + k]
            rows[top + k] = (r + RESET + " " * (col + start - full)
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


def set_decor(border=None, border_style="", art=None, art_scope="menus",
              behind=False, panel=False, shadow="", fade=None):
    """The theme's frame and corner art for present(): border is a BORDERS
    key or None; art the picture's sizes, biggest first, each a list of
    Pictures (see art.py), or None; art_scope "menus" or "everywhere";
    behind draws the art behind the text at full size (see overlay_art);
    panel draws it full size with the text in a bordered panel of its own,
    shadowed in `shadow` (a colour code)."""
    _decor.update(border=BORDERS.get(border), border_style=border_style,
                  art=art or None, art_scope=art_scope, behind=behind,
                  panel=panel, shadow=shadow, fade=fade)


def _panel(rows, text, width, top):
    """The text rows in a bordered box from row `top` at the left of the
    rows (the art), in the frame's border style, with a shaded drop
    shadow. Blank rows at the end of the text are left off."""
    content = list(text)
    while content and not visible_len(content[-1].rstrip()):
        content.pop()
    if not content or top < 0:
        return rows
    chars = _decor["border"] or BORDERS["rounded"]
    tl, tr, bl, br, across, down = chars
    style = _decor["border_style"]
    inner = min(width - 2 * len(down) - 1, max(visible_len(t) for t in content) + 1)
    height = min(len(rows) - 2 - top, len(content))
    side = style + down + RESET
    box = [style + tl + across * inner + tr + RESET]
    box += [side + pad(t, inner) + side for t in content[:height]]
    box += [style + bl + across * inner + br + RESET]
    out = list(rows)
    bw = inner + 2 * len(down)
    shade = (_decor["shadow"] or style) + "░" + RESET
    for k, line in enumerate(box):
        r = top + k
        if r < len(out):
            out[r] = _splice(out[r], 0, line)
        if 0 < k and r < len(out) and bw < width:
            out[r] = _splice(out[r], bw, shade)            # shadow down the right side
    r = top + len(box)
    if r < len(out):
        out[r] = _splice(out[r], 1, shade * min(bw, width - 1))   # and along the bottom
    return out


def repaint():
    """Draw the last frame again (after the overlay changed)."""
    if _last_frame:
        present(*_last_frame)


def set_overlay(lines):
    """A box (its lines, styled) to draw over the middle of every frame
    until it's set to None: a dialog over the screen behind it."""
    _overlay[:] = lines or []


def _over(rows, box):
    """The rows with the box laid over their middle."""
    rows = list(rows)
    bw = max(visible_len(b) for b in box)
    top = max(0, (len(rows) - len(box)) // 2)
    width = max((visible_len(r) for r in rows), default=0)
    left = max(0, (max(width, bw) - bw) // 2)
    for k, line in enumerate(box):
        r = top + k
        if r < len(rows):
            rows[r] = _splice(rows[r], left, pad(line, bw))
    return rows


def _splice(row, col, piece):
    """The row with piece written over it from column col."""
    cells = _cells(row)
    cells += [("", " ")] * max(0, col - len(cells))
    new = _cells(piece)
    cells = cells[:col] + new + cells[col + len(new):]
    out, cur = [], None
    for codes, ch in cells:
        if codes != cur:
            out.append(RESET + codes)
            cur = codes
        out.append(ch)
    return "".join(out) + RESET


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
