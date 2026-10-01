"""Keyboard input.

Every read goes through read_key(), which returns either a single printable
character or one of the key names below. Names are always longer than one
character, so `is_char` tells the two apart. Only this module touches msvcrt;
a POSIX backend would only need to replace `key_ready` and `_getch`.
"""

import ctypes
import msvcrt
import time
from ctypes import wintypes

from . import console

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
HOME, END, PGUP, PGDN = "home", "end", "pgup", "pgdn"
INSERT, DELETE = "insert", "delete"
ENTER, TAB, SHIFT_TAB, ESC = "enter", "tab", "shift-tab", "esc"
BACKSPACE, CTRL_BACKSPACE = "backspace", "ctrl-backspace"
CTRL_C, CTRL_D, CTRL_Q, CTRL_W = "ctrl-c", "ctrl-d", "ctrl-q", "ctrl-w"
UNKNOWN = "unknown"
RESIZE = "resize"   # not a key: the terminal changed size while waiting
POLL = 0.05

_CONTROL = {
    "\r": ENTER,
    "\t": TAB,
    "\x1b": ESC,
    "\x08": BACKSPACE,
    "\x7f": CTRL_BACKSPACE,
    "\x03": CTRL_C,
    "\x04": CTRL_D,
    "\x11": CTRL_Q,
    "\x17": CTRL_W,
}

# second code after a "\x00" / "\xe0" prefix
_EXTENDED = {
    "H": UP, "P": DOWN, "K": LEFT, "M": RIGHT,
    "G": HOME, "O": END, "I": PGUP, "Q": PGDN,
    "R": INSERT, "S": DELETE,
    "\x0f": SHIFT_TAB,
}

# final byte of an "ESC [ x" sequence, for consoles that send VT codes
_CSI = {
    "A": UP, "B": DOWN, "C": RIGHT, "D": LEFT,
    "H": HOME, "F": END, "Z": SHIFT_TAB,
}

VK_TAB = 0x09
VK_SHIFT = 0x10
SHIFT_PRESSED = 0x0010
KEY_EVENT = 0x0001


class _KeyRecord(ctypes.Structure):
    _fields_ = [("down", wintypes.BOOL), ("repeat", wintypes.WORD),
                ("vk", wintypes.WORD), ("scan", wintypes.WORD),
                ("char", wintypes.WCHAR), ("state", wintypes.DWORD)]


class _InputRecord(ctypes.Structure):
    _fields_ = [("type", wintypes.WORD), ("key", _KeyRecord)]


def key_ready():
    return msvcrt.kbhit()


def _getch():
    return msvcrt.getwch()


def _tab_with_shift():
    """Whether the next Tab waiting in the console input has Shift held.

    Shift-Tab arrives in three ways depending on the console: as the
    extended code 0x0f, as "ESC [ Z", or as a plain Tab whose key event
    has Shift set. The last one can only be seen by peeking at the raw
    input event before msvcrt reads it."""
    try:
        k32 = ctypes.windll.kernel32
        recs = (_InputRecord * 32)()
        n = wintypes.DWORD()
        if k32.PeekConsoleInputW(k32.GetStdHandle(-10), recs, 32, ctypes.byref(n)):
            for r in recs[:n.value]:
                if r.type == KEY_EVENT and r.key.down and r.key.vk == VK_TAB:
                    return bool(r.key.state & SHIFT_PRESSED)
    except (AttributeError, OSError):
        pass
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
    except (AttributeError, OSError):
        return False


def _escape_sequence():
    """After ESC: decode "ESC [ x" if one is arriving, otherwise it was a
    plain Esc press. Anything else read ahead is put back."""
    if not key_ready():
        return ESC
    c = _getch()
    if c != "[":
        msvcrt.ungetwch(c)
        return ESC
    return _CSI.get(_getch(), UNKNOWN)


def read_key(panic=True, resize=True):
    """Block for one key press. Ctrl-q is the global panic key: it wipes the
    screen and exits from anywhere unless panic is False. While waiting, a
    change of terminal size returns RESIZE so the caller can redraw."""
    if resize:
        start = console.size()
        while not key_ready():
            time.sleep(POLL)
            if console.size() != start:
                return RESIZE
    shift_tab = _tab_with_shift()      # must be read before the key is consumed
    c = _getch()
    if c in ("\x00", "\xe0"):
        key = _EXTENDED.get(_getch(), UNKNOWN)
    elif c == "\t":
        key = SHIFT_TAB if shift_tab else TAB
    elif c == "\x1b":
        key = _escape_sequence()
    elif c in _CONTROL:
        key = _CONTROL[c]
    elif c < " ":
        key = UNKNOWN
    else:
        key = c
    if panic and key == CTRL_Q:
        console.bail()
    return key


def is_char(key):
    """True for a printable character, False for a named key."""
    return len(key) == 1
