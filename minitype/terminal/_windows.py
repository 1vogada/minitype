"""Keyboard input on Windows, through msvcrt; the mouse through the
console's own input records.

With the mouse on (mouse()), the console sends mouse events as input
records next to the keys, and quick edit (selecting text with the mouse)
is off. msvcrt would read past them and drop them, so they're taken off
the front of the input first (_pump) and handed out as Mouse events; the
keys stay msvcrt's, decoded exactly as without the mouse. This works in
the classic console and in Windows Terminal (which passes the mouse to a
console app that asks for it); the VT input mode, which would bring the
mouse as escape sequences instead, stays off.
"""

import ctypes
import msvcrt
import time
from ctypes import wintypes

from .keynames import (BACKSPACE, CSI, CTRL_BACKSPACE, CTRL_C, CTRL_D, CTRL_O, CTRL_P, CTRL_I, CTRL_LBRACKET, CTRL_RBRACKET, CTRL_Q,
                       CTRL_W, DELETE, DOWN, END, ENTER, ESC, HOME, INSERT,
                       LEFT, PGDN, PGUP, RIGHT, SHIFT_ENTER, SHIFT_TAB, TAB,
                       UNKNOWN, UP, CLICK, HOVER, WHEEL_DOWN, WHEEL_UP, Mouse)

_CONTROL = {
    "\r": ENTER,
    "\t": TAB,
    "\x1b": ESC,
    "\x08": BACKSPACE,
    "\x7f": CTRL_BACKSPACE,
    "\x03": CTRL_C,
    "\x04": CTRL_D,
    "\x11": CTRL_Q,
    "\x0f": CTRL_O,
    "\x10": CTRL_P,
    "\x1d": CTRL_RBRACKET,
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
VK_I = 0x49
VK_LBRACKET = 0xDB   # the [ key (VK_OEM_4)
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_MENU = 0x12       # alt
SHIFT_PRESSED = 0x0010
KEY_EVENT = 0x0001
MOUSE_EVENT = 0x0002
# console input modes
ENABLE_MOUSE_INPUT = 0x0010
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080      # needed for a change to quick edit to count
# a mouse record's buttons and flags
LEFT_BUTTON = 0x0001
MOUSE_MOVED = 0x0001
MOUSE_WHEELED = 0x0004
WHEEL_NOTCH = 120                   # one notch of the wheel
PUMP = 64                           # input records looked at at a time
MOUSE_POLL = 0.002                  # a read waiting for a key, with the mouse on


class _KeyRecord(ctypes.Structure):
    _fields_ = [("down", wintypes.BOOL), ("repeat", wintypes.WORD),
                ("vk", wintypes.WORD), ("scan", wintypes.WORD),
                ("char", wintypes.WCHAR), ("state", wintypes.DWORD)]


class _MouseRecord(ctypes.Structure):
    _fields_ = [("x", wintypes.SHORT), ("y", wintypes.SHORT),
                ("buttons", wintypes.DWORD), ("state", wintypes.DWORD),
                ("flags", wintypes.DWORD)]


class _Event(ctypes.Union):
    _fields_ = [("key", _KeyRecord), ("mouse", _MouseRecord)]


class _InputRecord(ctypes.Structure):
    _anonymous_ = ("event",)
    _fields_ = [("type", wintypes.WORD), ("event", _Event)]


class _BufferInfo(ctypes.Structure):
    _fields_ = [("size", wintypes._COORD), ("cursor", wintypes._COORD),
                ("attributes", wintypes.WORD), ("window", wintypes.SMALL_RECT),
                ("biggest", wintypes._COORD)]


_mouse = {"on": False, "saved": None, "held": False, "wheel": 0}
_events = []            # mouse events taken off the input, not yet read


def setup():
    pass                    # the Windows console needs nothing switched on


def restore():
    mouse(False)


def mouse(on):
    """Switch the mouse on or off: the console's mouse input, with quick
    edit off while it's on (a click would start a selection instead).
    Off puts back the mode it had. Returns whether it's on - never when
    the input isn't a console."""
    on = bool(on)
    if on == _mouse["on"]:
        return on
    try:
        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-10)
        mode = wintypes.DWORD()
        if not k32.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        if on:
            _mouse["saved"] = mode.value
            new = (mode.value | ENABLE_MOUSE_INPUT | ENABLE_EXTENDED_FLAGS) \
                & ~ENABLE_QUICK_EDIT_MODE
        else:
            new = _mouse["saved"] | ENABLE_EXTENDED_FLAGS   # quick edit as it was
        if k32.SetConsoleMode(h, new):
            _mouse.update(on=on, held=False, wheel=0)
            _events.clear()
    except (AttributeError, OSError):
        pass
    return _mouse["on"]


def _window():
    """The visible window's top left in the console's buffer: mouse
    records count from the buffer's, which can have scrollback above."""
    try:
        k32 = ctypes.windll.kernel32
        info = _BufferInfo()
        if k32.GetConsoleScreenBufferInfo(k32.GetStdHandle(-11), ctypes.byref(info)):
            return info.window.Left, info.window.Top
    except (AttributeError, OSError):
        pass
    return 0, 0


def _decode(rec, origin=(0, 0)):
    """A mouse record as Mouse events: none for one that does nothing (a
    drag, a release, another button), a hover for a move, one for a click - the left button
    going down, the second click of a double click too - and one per notch
    for the wheel (a fast turn comes as one record of several notches; a
    touchpad's small turns add up to one)."""
    x, y = rec.x - origin[0], rec.y - origin[1]
    left = bool(rec.buttons & LEFT_BUTTON)
    if rec.flags & MOUSE_WHEELED:
        _mouse["wheel"] += ctypes.c_short((rec.buttons >> 16) & 0xFFFF).value
        notches = int(_mouse["wheel"] / WHEEL_NOTCH)          # towards 0
        _mouse["wheel"] -= notches * WHEEL_NOTCH
        return [Mouse(WHEEL_UP if notches > 0 else WHEEL_DOWN, x, y)] * abs(notches)
    if rec.flags & MOUSE_MOVED:
        _mouse["held"] = left                       # a drag isn't a click
        return [] if rec.buttons else [Mouse(HOVER, x, y)]
    pressed = left and not _mouse["held"]
    _mouse["held"] = left
    return [Mouse(CLICK, x, y)] if pressed else []


def _pump():
    """Take what isn't a key (mouse records, key releases, focus) off the
    front of the console input, keeping the mouse events. It stops at the
    first key, so msvcrt still reads every key itself."""
    try:
        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-10)
        recs = (_InputRecord * PUMP)()
        n = wintypes.DWORD()
        if not k32.PeekConsoleInputW(h, recs, PUMP, ctypes.byref(n)):
            return
        take, found = 0, []
        for r in recs[:n.value]:
            # a key, or an alt-code's character (on alt's release). Other
            # releases carry their character too but msvcrt passes over
            # them: left there, the mouse behind them would never be read
            if r.type == KEY_EVENT and (r.key.down or (r.key.vk == VK_MENU
                                                       and r.key.char not in ("", "\0"))):
                break
            take += 1
            if r.type == MOUSE_EVENT:
                found.append(_MouseRecord.from_buffer_copy(r.mouse))
        if take:
            origin = _window() if found else (0, 0)
            for m in found:
                _events.extend(_decode(m, origin))
            k32.ReadConsoleInputW(h, recs, take, ctypes.byref(n))
    except (AttributeError, OSError):
        pass


def ready():
    if _mouse["on"]:
        _pump()
    return bool(_events) or msvcrt.kbhit()


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


def _key_for(char):
    """The key (its virtual key code) behind the next waiting `char`, or
    None: the console sends ctrl-i as tab and ctrl-[ as esc, but its raw key
    event says which key it was."""
    try:
        k32 = ctypes.windll.kernel32
        recs = (_InputRecord * 32)()
        n = wintypes.DWORD()
        if k32.PeekConsoleInputW(k32.GetStdHandle(-10), recs, 32, ctypes.byref(n)):
            for r in recs[:n.value]:
                if r.type == KEY_EVENT and r.key.down and r.key.char == char:
                    return r.key.vk
    except (AttributeError, OSError):
        pass
    return None


def _ctrl_i():
    """Whether the tab character waiting came from ctrl-i, not the Tab key."""
    return _key_for("\t") == VK_I


def _ctrl_lbracket():
    """Whether the esc character waiting came from ctrl-[, not the Esc key."""
    return _key_for("\x1b") == VK_LBRACKET


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
    """One key press, decoded, or a mouse event (see mouse())."""
    while _mouse["on"] and not ready():
        time.sleep(MOUSE_POLL)          # msvcrt, blocking, would drop the mouse
    if _events:
        return _events.pop(0)
    # shift has to be read off the raw event before msvcrt consumes the key
    shift_tab = _with_shift(VK_TAB)
    shift_enter = _with_shift(VK_RETURN)
    ctrl_i = _ctrl_i()
    ctrl_lb = _ctrl_lbracket()
    c = _getch()
    if c in ("\x00", "\xe0"):
        return _EXTENDED.get(_getch(), UNKNOWN)
    if c == "\t":
        return CTRL_I if ctrl_i else SHIFT_TAB if shift_tab else TAB
    if c == "\r":
        return SHIFT_ENTER if shift_enter else ENTER
    if c == "\x1b":
        return CTRL_LBRACKET if ctrl_lb else _escape_sequence()
    if c in _CONTROL:
        return _CONTROL[c]
    if c < " ":
        return UNKNOWN
    return c
