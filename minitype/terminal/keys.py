"""Keyboard input.

Every read goes through read_key(), which returns either a single printable
character or one of the key names below. Names are always longer than one
character, so `is_char` tells the two apart.

The reading itself is done by a back end: _windows (msvcrt) on Windows,
_posix (termios) on Linux and macOS. Call setup() before reading keys and
restore() when done; on Linux and macOS that switches the terminal into
raw mode and back.
"""

import atexit
import os
import time

from . import console
from .keynames import (BACKSPACE, CTRL_BACKSPACE, CTRL_C, CTRL_D, CTRL_Q,
                       CTRL_W, DELETE, DOWN, END, ENTER, ESC, HOME, INSERT,
                       LEFT, PGDN, PGUP, RESIZE, RIGHT, SHIFT_ENTER, SHIFT_TAB,
                       TAB, UNKNOWN, UP)

__all__ = [
    "UP", "DOWN", "LEFT", "RIGHT", "HOME", "END", "PGUP", "PGDN", "INSERT",
    "DELETE", "ENTER", "SHIFT_ENTER", "TAB", "SHIFT_TAB", "ESC", "BACKSPACE",
    "CTRL_BACKSPACE", "CTRL_C", "CTRL_D", "CTRL_Q", "CTRL_W", "UNKNOWN",
    "RESIZE", "setup", "restore", "key_ready", "read_key", "is_char",
]

if os.name == "nt":
    from . import _windows as backend
else:
    from . import _posix as backend

POLL = 0.05


def setup():
    backend.setup()
    atexit.register(backend.restore)


def restore():
    backend.restore()


def key_ready():
    return backend.ready()


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
    key = backend.read()
    if panic and key == CTRL_Q:
        console.bail()
    return key


def is_char(key):
    """True for a printable character, False for a named key."""
    return len(key) == 1
