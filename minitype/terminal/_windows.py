"""Keyboard input on Windows, through msvcrt."""

import ctypes
import msvcrt
from ctypes import wintypes

from .keynames import (BACKSPACE, CSI, CTRL_BACKSPACE, CTRL_C, CTRL_D, CTRL_Q,
                       CTRL_W, DELETE, DOWN, END, ENTER, ESC, HOME, INSERT,
                       LEFT, PGDN, PGUP, RIGHT, SHIFT_ENTER, SHIFT_TAB, TAB,
                       UNKNOWN, UP)

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

VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
SHIFT_PRESSED = 0x0010
KEY_EVENT = 0x0001


class _KeyRecord(ctypes.Structure):
    _fields_ = [("down", wintypes.BOOL), ("repeat", wintypes.WORD),
                ("vk", wintypes.WORD), ("scan", wintypes.WORD),
                ("char", wintypes.WCHAR), ("state", wintypes.DWORD)]


class _InputRecord(ctypes.Structure):
    _fields_ = [("type", wintypes.WORD), ("key", _KeyRecord)]


def setup():
    pass                    # the Windows console needs nothing switched on


def restore():
    pass


def ready():
    return msvcrt.kbhit()


def _getch():
    return msvcrt.getwch()


def _with_shift(vk):
    """Whether the next key `vk` waiting in the console input has Shift
    held.

    msvcrt gives Tab and Enter the same character with or without Shift
    (some consoles send Shift-Tab as the extended code 0x0f or "ESC [ Z",
    but not all). The Shift flag is on the raw key event, which can be
    peeked at before msvcrt reads it."""
    try:
        k32 = ctypes.windll.kernel32
        recs = (_InputRecord * 32)()
        n = wintypes.DWORD()
        if k32.PeekConsoleInputW(k32.GetStdHandle(-10), recs, 32, ctypes.byref(n)):
            for r in recs[:n.value]:
                if r.type == KEY_EVENT and r.key.down and r.key.vk == vk:
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
    if not ready():
        return ESC
    c = _getch()
    if c != "[":
        msvcrt.ungetwch(c)
        return ESC
    return CSI.get(_getch(), UNKNOWN)


def read():
    """One key press, decoded."""
    # shift has to be read off the raw event before msvcrt consumes the key
    shift_tab = _with_shift(VK_TAB)
    shift_enter = _with_shift(VK_RETURN)
    c = _getch()
    if c in ("\x00", "\xe0"):
        return _EXTENDED.get(_getch(), UNKNOWN)
    if c == "\t":
        return SHIFT_TAB if shift_tab else TAB
    if c == "\r":
        return SHIFT_ENTER if shift_enter else ENTER
    if c == "\x1b":
        return _escape_sequence()
    if c in _CONTROL:
        return _CONTROL[c]
    if c < " ":
        return UNKNOWN
    return c
