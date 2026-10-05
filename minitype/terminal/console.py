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
    write("\x1b[2J\x1b[H")


def bell():
    write("\a")


def size():
    """(columns, rows), never smaller than the minimum we can draw in."""
    s = shutil.get_terminal_size((80, 24))
    return max(MIN_W, s.columns), max(MIN_H, s.lines)


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


def present(lines, focus=None, pinned=()):
    """Draw a whole frame in place. Lines are clipped to the terminal width;
    if there are more than fit, the view scrolls to keep line `focus` on
    screen. `pinned` lines stick to the bottom when there's room for them.
    A resize clears the screen first so no old content is left behind."""
    global _last_size
    w, h = size()
    if (w, h) != _last_size:
        write("\x1b[2J")
        _last_size = (w, h)
    pinned = list(pinned) if len(pinned) < h - 2 else []
    body_h = h - len(pinned)
    lines = list(lines)
    top = 0
    if len(lines) > body_h:
        f = focus if focus is not None else 0
        top = max(0, min(f - body_h // 2, len(lines) - body_h))
    view = lines[top:top + body_h]
    view += [""] * (body_h - len(view)) if pinned else []
    view += pinned
    out = "\x1b[K\n".join(clip(line, w - 1) + RESET for line in view)
    write("\x1b[H" + out + "\x1b[K\x1b[J")
    flush()


def bail():
    """Panic exit: wipe the screen and drop out, leaving no scrollback."""
    clear()
    cursor(True)
    flush()
    raise SystemExit
