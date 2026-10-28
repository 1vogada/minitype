"""Keyboard input.

Every read goes through read_key(), which returns either a single printable
character or one of the key names below. Names are always longer than one
character, so `is_char` tells the two apart.

The reading itself is done by a back end: _windows (msvcrt) on Windows,
_posix (termios) on Linux and macOS. Call setup() before reading keys and
restore() when done; on Linux and macOS that switches the terminal into
raw mode and back.

The mouse (mouse(), the mouse setting) comes through read_key too: the
wheel as up and down, a click as whatever the thing clicked stands for
(console.hit) - a menu row's enter - and pointing at something as a
redraw (RESIZE) when that changed the screen (a menu row is selected, as
the arrows would). A click on nothing, the mouse still pointing where it
was, and anything else the mouse does, is passed over. While a test runs (stamping) the mouse is
passed over altogether, so it never counts as a key; a box over the test
(the pause box, ctrl-o's settings: over_test) can still be clicked. A
click left waiting when the test ends is dropped, not handed to the next
screen.
"""

import atexit
import os
import queue
import sys
import threading
import time

from . import console
from .keynames import (BACKSPACE, CTRL_BACKSPACE, CTRL_C, CTRL_D, CTRL_O, CTRL_P, CTRL_I, CTRL_LBRACKET, CTRL_RBRACKET, CTRL_Q,
                       CTRL_W, DELETE, DOWN, END, ENTER, ESC, HOME, INSERT,
                       LEFT, PGDN, PGUP, RESIZE, RIGHT, SHIFT_ENTER, SHIFT_TAB,
                       TAB, UNKNOWN, UP, CLICK, HOVER, WHEEL_DOWN, WHEEL_UP, Mouse)

__all__ = [
    "UP", "DOWN", "LEFT", "RIGHT", "HOME", "END", "PGUP", "PGDN", "INSERT",
    "DELETE", "ENTER", "SHIFT_ENTER", "TAB", "SHIFT_TAB", "ESC", "BACKSPACE",
    "CTRL_BACKSPACE", "CTRL_C", "CTRL_D", "CTRL_O", "CTRL_P", "CTRL_I", "CTRL_LBRACKET", "CTRL_RBRACKET", "CTRL_Q", "CTRL_W", "UNKNOWN",
    "RESIZE", "setup", "restore", "key_ready", "read_key", "is_char",
    "on_settings_key", "stamping", "key_time", "mouse",
]

if os.name == "nt":
    from . import _windows as backend
else:
    from . import _posix as backend

POLL = 0.002           # how often a waiting read looks for a key
SIZE_POLL = 0.05       # how often it looks for a resized terminal


# the mouse setting, and whether the terminal is ours to change (between
# setup and restore: never in the tests, which only draw)
_mouse = {"want": False, "live": False, "at": None}   # at: the cell last pointed at


def setup():
    backend.setup()
    atexit.register(backend.restore)
    _mouse["live"] = True
    mouse(_mouse["want"])


def restore():
    backend.restore()
    _mouse["live"] = False
    console.set_clickable(False)


def mouse(on):
    """The mouse on or off (the mouse setting). Things drawn with
    console.hit can be clicked while it's on - where the terminal can
    report the mouse at all, and only after setup(). Returns whether it's
    on."""
    _mouse["want"] = bool(on)
    on = backend.mouse(on) if _mouse["live"] else False
    console.set_clickable(on)
    return on


# While a test runs, a thread reads the keys and notes when each came, so
# a slow frame doesn't make your typing look slow: the test goes by when
# you pressed a key, not when it got round to it. Keys read and not yet
# taken wait in _stamped, and read_key takes them from there first.
_stamped = queue.Queue()
_stamper = {"thread": None, "stop": None,
            "typing": False}    # a test is reading the keys: the mouse is passed over
_last = {"t": 0.0}      # when the key read_key last returned came
STAMP_POLL = 0.0005     # how often the thread looks for a key
SWITCH = 0.001          # how often python lets the thread in while a test runs


def _stamp(stop):
    while not stop.is_set():
        if backend.ready():
            _stamped.put((backend.read(), time.time()))
        else:
            time.sleep(STAMP_POLL)


def _drop_mouse(everywhere=False):
    """Throw away the mouse events waiting at the front of the timed keys
    (or all of them): a test reads past them, so the mouse never counts as
    a key - only a box over it (pause, ctrl-o: see over_test) takes them."""
    with _stamped.mutex:
        waiting = _stamped.queue
        if everywhere:
            kept = [k for k in waiting if not isinstance(k[0], Mouse)]
            waiting.clear()
            waiting.extend(kept)
        while waiting and isinstance(waiting[0][0], Mouse):
            waiting.popleft()


class stamping:
    """with keys.stamping(): ... keys are read and timed in the background
    (see key_time), for a test: the mouse is passed over meanwhile."""

    def __enter__(self):
        self._typing = _stamper["typing"]
        _stamper["typing"] = True
        if _stamper["thread"] is None:
            stop = threading.Event()
            self._switch = sys.getswitchinterval()
            sys.setswitchinterval(SWITCH)
            t = threading.Thread(target=_stamp, args=(stop,), daemon=True)
            _stamper.update(thread=t, stop=stop)
            self.own = True
            t.start()
        else:
            self.own = False                # already on (a test inside a test)
        return self

    def __exit__(self, *exc):
        _stamper["typing"] = self._typing
        if self.own:
            _stamper["stop"].set()
            _stamper["thread"].join()
            _stamper.update(thread=None, stop=None)
            sys.setswitchinterval(self._switch)
            _drop_mouse(everywhere=True)    # a click while typing isn't for the next screen
        return False


class over_test:
    """with keys.over_test(): ... a box drawn over a test (the pause box,
    ctrl-o's settings) takes the mouse while the test waits under it."""

    def __enter__(self):
        self._typing = _stamper["typing"]
        _stamper["typing"] = False
        return self

    def __exit__(self, *exc):
        _stamper["typing"] = self._typing
        return False


def key_ready():
    if _stamper["typing"]:
        _drop_mouse()
    return not _stamped.empty() or (_stamper["thread"] is None and backend.ready())


def key_time():
    """When the key read_key last returned was pressed (as time.time())."""
    return _last["t"]


def _next_key():
    try:
        key, _last["t"] = _stamped.get_nowait()
        return key
    except queue.Empty:
        pass
    if _stamper["thread"] is not None:
        key, _last["t"] = _stamped.get()
        return key
    key = backend.read()
    _last["t"] = time.time()
    return key


_settings = {"open": None, "busy": False}


def on_settings_key(fn):
    """What ctrl-o does from anywhere (open the settings): fn() is called
    from inside read_key, which then returns RESIZE so the screen redraws.
    Not again while it's already open."""
    _settings["open"] = fn


def _from_mouse(event):
    """The key a mouse event stands for (see the module notes), or None."""
    if event == WHEEL_UP:
        return UP
    if event == WHEEL_DOWN:
        return DOWN
    if event == CLICK:
        hit, key = console.click(event.x, event.y)
        if hit:
            return key or RESIZE
    if event == HOVER and (event.x, event.y) != _mouse["at"]:
        _mouse["at"] = (event.x, event.y)
        if console.hover(event.x, event.y):
            return RESIZE
    return None


def read_key(panic=True, resize=True):
    """Block for one key press. Ctrl-q is the global panic key: it wipes the
    screen and exits from anywhere unless panic is False. Ctrl-o opens the
    settings from anywhere (see on_settings_key). While waiting, a change of
    terminal size returns RESIZE so the caller can redraw. The mouse comes
    as keys too (see the module notes)."""
    start = console.size() if resize else None
    while True:
        if resize:
            checked = time.monotonic()
            while not key_ready():
                time.sleep(POLL)
                now = time.monotonic()
                if now - checked >= SIZE_POLL:
                    checked = now
                    if console.size() != start:
                        return RESIZE
        elif _stamper["typing"]:
            _drop_mouse()
        key = _next_key()
        if not isinstance(key, Mouse):
            break
        key = None if _stamper["typing"] else _from_mouse(key)
        if key is not None:
            return key
    if panic and key == CTRL_Q:
        console.bail()
    if key == CTRL_O and _settings["open"] and not _settings["busy"]:
        _settings["busy"] = True
        try:
            _settings["open"]()
        finally:
            _settings["busy"] = False
        return RESIZE
    return key


def is_char(key):
    """True for a printable character, False for a named key."""
    return len(key) == 1
