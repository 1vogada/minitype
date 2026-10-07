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
          "behind": False, "panel": False, "shadow": "", "fade": None, "text_fx": None,
          "see_through": 0.4, "menu_lighten": 0.0}
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
    lighten = _decor.get("menu_lighten") or 0
    if lighten and scene != "test":
        # menu text a shade lighter - only the letters' own colour: the
        # border, background and art are put on after this
        lines = [_lighter(line, lighten) for line in lines]
        pinned = [_lighter(line, lighten) for line in pinned]
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
        boxed, dim = _panel([""] * len(rows), body, w - 1, 0)
        if hints:
            boxed, more = _panel(boxed, hints, w - 1, len(rows) - len(hints) - 2)
            dim.update(more)
        rows = overlay_art(boxed, art, w - 1, 0, True, dim)
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


def _lum(c):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])


def _contrast(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


READABLE = 4.5          # the contrast a nudged letter is brought up to (WCAG AA)


@lru_cache(maxsize=4096)
def _readable(codes, under, fx):
    """A letter's codes as it's printed over an art cell whose background
    is `under`: with the text contrast setting applied - nudge moves its
    colour lighter or darker (the same hue) just until it reads against
    the art, flip swaps it for the theme's darkest or lightest colour,
    whichever reads better - and in bold if that's on."""
    from .style import rgb_of_code            # style draws through this module
    mode, bold, dark, light = fx
    out = codes
    bg = rgb_of_code(under, 48)
    if mode != "off" and bg:
        fg = rgb_of_code(codes) or (220, 220, 220)
        if mode == "flip":
            new = dark if _contrast(dark, bg) > _contrast(light, bg) else light
        else:
            new = fg
            if _contrast(fg, bg) < READABLE:
                to = (255, 255, 255) if _contrast((255, 255, 255), bg) >= _contrast((0, 0, 0), bg) else (0, 0, 0)
                for k in range(1, 21):
                    new = tuple(int(a + (b - a) * k / 20) for a, b in zip(fg, to))
                    if _contrast(new, bg) >= READABLE:
                        break
        out += "\x1b[38;2;%d;%d;%dm" % new
    if bold:
        out += "\x1b[1m"
    return out


def _see_through():
    """How bright the art shows through a box over it (the see-through
    setting), 0..1."""
    return _decor.get("see_through", 0.4)


def _scrim(cell, keep=None):
    """A background for a help box over this art cell: the art's own
    colour darkened (its background, else its ink), so the picture still
    shows faintly through the box instead of a black hole; "" over blank
    art or colours that aren't truecolour."""
    codes, ch = cell
    m = re.findall(r"\x1b\[48;2;(\d+);(\d+);(\d+)m", codes) or \
        re.findall(r"\x1b\[38;2;(\d+);(\d+);(\d+)m", codes)
    if not m:
        return ""
    keep = _see_through() if keep is None else keep
    r, g, b = (int(int(v) * keep) for v in m[-1])
    return f"\x1b[48;2;{r};{g};{b}m"


@lru_cache(maxsize=8192)
def _dimmed(codes, keep):
    """An art cell's codes with every truecolour in them darkened."""
    return re.sub(r"(38|48);2;(\d+);(\d+);(\d+)",
                  lambda m: "%s;2;%d;%d;%d" % (m.group(1), *(int(int(v) * keep) for v in m.groups()[1:])),
                  codes)


def _layer(row, pic, card, dim=None):
    """The row drawn over a row of the art (cells from _art_cells). The art
    shows through wherever the row has a plain blank; letters, and blanks
    with a highlight or background of their own, cover it. `card` is the
    (from, to) columns of floating text (a help box), which covers the art
    whole, in a darkened shade of the art behind it (see _scrim). `dim`
    is the (from, to) columns of a text panel: the art shows through it,
    darkened (see _dimmed)."""
    text = _cells(row)
    out, cur = [], None
    for x in range(max(len(text), len(pic))):
        t = text[x] if x < len(text) else ("", " ")
        a = pic[x] if x < len(pic) else ("", " ")
        if dim and dim[0] <= x < dim[1] and a[0]:
            a = (_dimmed(a[0], _see_through()), a[1])
        solid = (t[1] != " " or "\x1b[7m" in t[0] or "\x1b[48;" in t[0]
                 or card[0] <= x < card[1])
        codes, ch = t if solid or (a[1] == " " and not a[0]) else a
        if card[0] <= x < card[1] and "\x1b[48;" not in t[0] and "\x1b[7m" not in t[0]:
            codes = t[0] + _scrim(a)
            fx = _decor.get("text_fx")
            if fx and (fx[0] != "off" or fx[1]) and t[1] != " ":
                codes = _readable(t[0], _scrim(a), fx) + _scrim(a)
        if solid and t[1] != " " and not card[0] <= x < card[1] and "\x1b[48;" not in t[0] \
                and "\x1b[7m" not in t[0]:
            codes = t[0] + _behind(a)         # printed on the art, not punched out of it
            fx = _decor.get("text_fx")
            if fx and (fx[0] != "off" or fx[1]):
                codes = _readable(t[0], _behind(a), fx) + _behind(a)
        if codes != cur:
            out.append(RESET + codes)
            cur = codes
        out.append(ch)
    return "".join(out).rstrip() + RESET


def overlay_art(rows, versions, width, pinned_n, behind=False, dim=None):
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
    by letter, and only floating text gets a solid card. It fills the
    screen edge to edge: down to the last row (behind the key hints too),
    the full width, and its sky carried on up to the top row. `dim` maps
    a row to the (from, to) columns where the art is dimmed (a text
    panel over it)."""
    if behind:
        bottom, avail = len(rows) - 1, width
        for pic in [pic.wider(avail) for pic in versions]:
            w = min(pic.width, avail) if pic.span else pic.width
            top, col = bottom - pic.height + 1, avail - w
            if top < 0 or col < 0:
                continue
            pic = _dressed(pic, top, whole=True)
            top -= pic.extra
            rows = list(rows)
            for k in range(pic.height):
                r = rows[top + k]
                i = r.find(FLOAT)
                card = (visible_len(r[:i]), visible_len(r)) if i >= 0 else (0, 0)
                rows[top + k] = _layer(r, _art_cells(pic, k, pic.width - w, col), card,
                                       (dim or {}).get(top + k))
            return rows
        return rows
    bottom = len(rows) - pinned_n - (2 if pinned_n else 1)
    avail = width - 1
    # on a screen wider than a spanning picture, its scenery grows to fill it
    for pic in [pic.wider(avail) for pic in versions]:
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
        box = min(starts) - col
        pic = _dressed(pic, top - 1)
        top -= pic.extra
        spans = [_text_ends(rows[top + k]) for k in range(pic.height)]
        ends = [solid for solid, _ in spans]
        # the background only runs the full width below the last text;
        # beside text it keeps to the picture's own box
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


def _dressed(pic, room, whole=False):
    """The picture as it's drawn: with filler on top (up to art.TALLER of
    its height - or, `whole`, all the way up - as far as the `room` above
    it goes; the filler never decides whether it fits) and faded into the
    screen if that's on."""
    from .art import TALLER
    pic = pic.taller(room if whole else min(room, int(pic.height * TALLER)))
    fade = _decor.get("fade")
    if fade and fade[0] != "off" and getattr(pic, "back", False):
        pic = pic.faded(*fade)      # pictures with backgrounds dissolve at their edges
    return pic


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
              behind=False, panel=False, shadow="", fade=None, text_fx=None,
              see_through=0.4, menu_lighten=0.0):
    """The theme's frame and corner art for present(): border is a BORDERS
    key or None; art the picture's sizes, biggest first, each a list of
    Pictures (see art.py), or None; art_scope "menus" or "everywhere";
    behind draws the art behind the text at full size (see overlay_art);
    panel draws it full size with the text in a bordered panel of its own,
    shadowed in `shadow` (a colour code). text_fx is (contrast, bold,
    darkest, lightest) for letters drawn over the art (see _readable);
    see_through how much of the art shows through boxes over it, 0..1;
    menu_lighten how far towards white menu text is drawn, 0..1."""
    _decor.update(border=BORDERS.get(border), border_style=border_style,
                  art=art or None, art_scope=art_scope, behind=behind,
                  panel=panel, shadow=shadow, fade=fade, text_fx=text_fx,
                  see_through=see_through, menu_lighten=menu_lighten)


def _panel(rows, text, width, top):
    """The text rows in a bordered box from row `top` at the left of the
    rows, in the frame's border style, as wide as the text itself (help
    floating beside it doesn't count: it goes over the box's edge as a
    card). Returns (rows, dim): dim maps each row of the box to the
    columns it covers, where the art behind shows through darkened. Blank
    rows at the end of the text are left off."""
    content = list(text)
    while content and not visible_len(content[-1].rstrip()):
        content.pop()
    if not content or top < 0:
        return rows, {}
    chars = _decor["border"] or BORDERS["rounded"]
    tl, tr, bl, br, across, down = chars
    style = _decor["border_style"]
    side = style + down + RESET

    def solid(line):
        i = line.find(FLOAT)
        return line if i < 0 else line[:i]

    def used(line):
        cells = _cells(solid(line))
        return max((k + 1 for k, (_, ch) in enumerate(cells) if ch != " "), default=0)
    inner = min(width - 2 * len(down) - 1, max(used(t) for t in content) + 1)
    height = min(len(rows) - 2 - top, len(content))
    box = [style + tl + across * inner + tr + RESET]
    for t in content[:height]:
        line = side + pad(solid(t), inner) + side
        i = t.find(FLOAT)
        if i >= 0:                                 # help floating beside the text
            at = len(down) + visible_len(t[:i])
            line = clip(line, at) + " " * max(0, at - visible_len(line)) + t[i:]
        box.append(line)
    box.append(style + bl + across * inner + br + RESET)
    out, dim = list(rows), {}
    bw = inner + 2 * len(down)
    for k, line in enumerate(box):
        r = top + k
        if r < len(out):
            out[r] = line
            dim[r] = (0, bw)
    return out, dim


_CSI = re.compile(r"\x1b\[([0-9;]*)m")


@lru_cache(maxsize=4096)
def _lighter_seq(params, t):
    """One escape sequence's parameters with its text colour (38;2 / 38;5)
    moved t of the way to white; backgrounds and the rest untouched."""
    from .style import rgb_of_256
    nums = params.split(";")
    out, i = [], 0
    while i < len(nums):
        n = nums[i]
        if n in ("38", "48") and i + 1 < len(nums) and nums[i + 1] in ("2", "5"):
            size = 5 if nums[i + 1] == "2" else 3
            part = nums[i:i + size]
            if n == "38" and len(part) == size:
                rgb = tuple(int(v) for v in part[2:]) if size == 5 else rgb_of_256(int(part[2]))
                rgb = tuple(int(c + (255 - c) * t) for c in rgb)
                part = ["38", "2"] + [str(c) for c in rgb]
            out += part
            i += size
            continue
        out.append(n)
        i += 1
    return ";".join(out)


def _lighter(line, t):
    """The line with every text colour in it moved t towards white."""
    return _CSI.sub(lambda m: "\x1b[" + _lighter_seq(m.group(1), t) + "m", line)


def repaint():
    """Draw the last frame again (after the overlay changed)."""
    if _last_frame:
        present(*_last_frame)


def set_overlay(lines):
    """A box (its lines, styled) to draw over the middle of every frame
    until it's set to None: a dialog over the screen behind it."""
    _overlay[:] = lines or []


def _over(rows, box):
    """The rows with the box laid over their middle. Where it covers the
    art, the art shows through the box darkened (the see-through setting),
    instead of a black hole; the box's own highlights stay as they are."""
    rows = list(rows)
    bw = max(visible_len(b) for b in box)
    top = max(0, (len(rows) - len(box)) // 2)
    width = max((visible_len(r) for r in rows), default=0)
    left = max(0, (max(width, bw) - bw) // 2)
    keep = _see_through()
    for k, line in enumerate(box):
        r = top + k
        if r >= len(rows):
            continue
        under = _cells(rows[r])
        new = []
        for j, (codes, ch) in enumerate(_cells(pad(line, bw))):
            u = under[left + j] if left + j < len(under) else ("", " ")
            if "\x1b[48;" not in codes and "\x1b[7m" not in codes:
                codes = codes + _dimmed(_behind(u), keep)
            new.append((codes, ch))
        rows[r] = _splice(rows[r], left, "".join(RESET + c + ch for c, ch in new))
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
