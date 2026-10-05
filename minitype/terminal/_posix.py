"""Keyboard input on Linux and macOS.

The terminal is switched into raw mode while minitype runs: no echo, no
line buffering, and ctrl-c / ctrl-q arrive as keys instead of signals or
flow control. restore() puts it back, and runs on exit.

Keys arrive as bytes. Special keys are escape sequences: "ESC [ A" for up,
"ESC [ 5 ~" for page up, and so on. Backspace is 0x7f here (0x08 on
Windows), and ctrl- or alt-backspace send 0x08 or "ESC 0x7f".

Plain terminals send the same byte for enter and shift-enter. Terminals
that report modified keys (kitty, wezterm, foot, iTerm2 with CSI u, or
xterm's modifyOtherKeys) send a separate sequence, which is decoded.
"""

import os
import select
import sys

from .keynames import (BACKSPACE, CSI, CTRL_BACKSPACE, CTRL_C, CTRL_D, CTRL_Q,
                       CTRL_W, DELETE, END, ENTER, ESC, HOME, INSERT, PGDN,
                       PGUP, SHIFT_ENTER, SHIFT_TAB, TAB, UNKNOWN)

ESC_WAIT = 0.03         # seconds to wait for the rest of an escape sequence
MAX_PARAMS = 16

_CONTROL = {
    "\r": ENTER,
    "\n": ENTER,
    "\t": TAB,
    "\x7f": BACKSPACE,
    "\x08": CTRL_BACKSPACE,
    "\x03": CTRL_C,
    "\x04": CTRL_D,
    "\x11": CTRL_Q,
    "\x17": CTRL_W,
}

# "ESC [ n ~" sequences
_TILDE = {
    "1": HOME, "7": HOME, "4": END, "8": END,
    "2": INSERT, "3": DELETE, "5": PGUP, "6": PGDN,
}

# "ESC [ code ; mods u" (and xterm's "ESC [ 27 ; mods ; code ~"): the key
# code, and what it is with shift (mods 2) or ctrl (mods 5)
_MODIFIED = {
    13: (ENTER, SHIFT_ENTER, ENTER),
    9: (TAB, SHIFT_TAB, TAB),
    127: (BACKSPACE, BACKSPACE, CTRL_BACKSPACE),
    27: (ESC, ESC, ESC),
}

_fd = None
_saved = None
_pending = []           # characters read ahead and put back


def setup():
    """Raw mode, if stdin is a terminal."""
    global _fd, _saved
    if _saved is not None or not sys.stdin.isatty():
        return
    import termios
    _fd = sys.stdin.fileno()
    _saved = termios.tcgetattr(_fd)
    mode = termios.tcgetattr(_fd)
    mode[0] &= ~(termios.IXON | termios.ICRNL | termios.INLCR | termios.ISTRIP)
    mode[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG | termios.IEXTEN)
    mode[6][termios.VMIN] = 1
    mode[6][termios.VTIME] = 0
    termios.tcsetattr(_fd, termios.TCSANOW, mode)


def restore():
    global _saved
    if _saved is None:
        return
    import termios
    termios.tcsetattr(_fd, termios.TCSADRAIN, _saved)
    _saved = None


def _fileno():
    return _fd if _fd is not None else sys.stdin.fileno()


def ready(timeout=0):
    if _pending:
        return True
    r, _, _ = select.select([_fileno()], [], [], timeout)
    return bool(r)


def _read_byte():
    return os.read(_fileno(), 1)


def _getch():
    """One character, decoding UTF-8 so Cyrillic and accents come through."""
    if _pending:
        return _pending.pop(0)
    b = _read_byte()
    if not b:
        return "\x04"                       # end of input: treat as ctrl-d
    lead = b[0]
    more = 3 if lead >= 0xF0 else 2 if lead >= 0xE0 else 1 if lead >= 0xC0 else 0
    for _ in range(more):
        b += _read_byte()
    return b.decode("utf-8", errors="replace")


def _modified(code, mods):
    keys = _MODIFIED.get(code)
    if keys is None:
        return chr(code) if 32 <= code < 0x110000 and mods <= 2 else UNKNOWN
    bits = mods - 1                 # 1 shift, 2 alt, 4 ctrl
    if bits & 4:
        return keys[2]
    if bits & 1:
        return keys[1]
    return keys[0]


def _csi():
    params = ""
    while True:
        c = _getch()
        if "\x40" <= c <= "\x7e":
            final = c
            break
        params += c
        if len(params) > MAX_PARAMS:
            return UNKNOWN
    nums = [int(p) if p.isdigit() else 1 for p in params.split(";")] if params else []
    if final == "~":
        if len(nums) == 3 and nums[0] == 27:           # xterm modifyOtherKeys
            return _modified(nums[2], nums[1])
        return _TILDE.get(params.split(";")[0], UNKNOWN)
    if final == "u" and nums:                          # CSI u
        return _modified(nums[0], nums[1] if len(nums) > 1 else 1)
    return CSI.get(final, UNKNOWN)


def _escape():
    """After ESC: a sequence if more is already arriving, else plain Esc."""
    if not ready(ESC_WAIT):
        return ESC
    c = _getch()
    if c == "[":
        return _csi()
    if c == "O":                       # SS3, application-mode arrows
        return CSI.get(_getch(), UNKNOWN)
    if c in ("\x7f", "\x08"):          # alt-backspace: delete a word
        return CTRL_BACKSPACE
    _pending.insert(0, c)
    return ESC


def read():
    """One key press, decoded."""
    c = _getch()
    if c == "\x1b":
        return _escape()
    if c in _CONTROL:
        return _CONTROL[c]
    if c < " ":
        return UNKNOWN
    return c
