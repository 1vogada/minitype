"""Keyboard input.

Every read goes through read_key(), which returns either a single printable
character or one of the key names below. Names are always longer than one
character, so `is_char` tells the two apart. Only this module touches msvcrt;
a POSIX backend would only need to replace `key_ready` and `_getch`.
"""

import msvcrt
import time

from . import console

UP, DOWN, LEFT, RIGHT = "up", "down", "left", "right"
HOME, END, PGUP, PGDN = "home", "end", "pgup", "pgdn"
INSERT, DELETE = "insert", "delete"
ENTER, TAB, ESC = "enter", "tab", "esc"
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
}


def key_ready():
    return msvcrt.kbhit()


def _getch():
    return msvcrt.getwch()


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
    c = _getch()
    if c in ("\x00", "\xe0"):
        key = _EXTENDED.get(_getch(), UNKNOWN)
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
