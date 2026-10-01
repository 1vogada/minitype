"""Console output: ANSI setup, screen and cursor control."""

import ctypes
import shutil
import sys


def enable_vt():
    """Turn on ANSI escape processing in the Windows console."""
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


def width():
    """Usable width for the word display."""
    return max(30, shutil.get_terminal_size((80, 24)).columns - 4)


def bail():
    """Panic exit: wipe the screen and drop out, leaving no scrollback."""
    clear()
    cursor(True)
    flush()
    raise SystemExit


def bell():
    write("\a")
