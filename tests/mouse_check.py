"""The mouse (the mouse setting): clicks and the wheel, from the terminal's
reports to what they do on screen. A fake back end feeds mouse events
through the real read_key, console.click and menus; where to click is read
off the frames as drawn (border, text panel and all). Then the two real
back ends: Windows (console input records, quick edit, the mode put back)
and Linux / macOS (SGR reports); and the test's own key reader, which never
counts the mouse as a key."""
import ctypes
import os
import re
import sys
import tempfile
import time

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock                                    # noqa: E402
from minitype.engine.spec import TestSpec                    # noqa: E402
from minitype.terminal import _posix, console, keys          # noqa: E402
from minitype.terminal.keynames import CLICK, HOVER, MOUSE, WHEEL_DOWN, WHEEL_UP, Mouse   # noqa: E402
from minitype.context import App                             # noqa: E402
from minitype.ui import anywhere                             # noqa: E402
from minitype.ui import main_menu as mm                      # noqa: E402
from minitype.ui import settings_menu as sm                  # noqa: E402
from minitype.ui.menu import Menu                            # noqa: E402
from minitype.ui.screen import menu_loop                     # noqa: E402
from minitype.ui.tree_menu import TreeMenu                   # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)


class Fake:
    """A back end reading from a list: keys, Mouse events, or functions
    giving one when it's read (so a click can be aimed at the frame drawn
    just before)."""

    def __init__(self):
        self.q, self.on = [], False

    def setup(self):
        pass

    def restore(self):
        self.mouse(False)

    def mouse(self, on):
        self.on = bool(on)
        return self.on

    def ready(self):
        return bool(self.q)

    def read(self):
        e = self.q.pop(0)
        return e() if callable(e) else e


fake = Fake()
keys.backend = fake
keys.mouse(True)
assert not fake.on and not console.clickable(), "before setup the terminal isn't touched"
keys.setup()
assert fake.on, "setup puts the setting asked for before it into effect"
out = []
console.write, console.flush = out.append, lambda: None


def frame():
    """The last frame drawn, as plain text lines (row 0 at the top)."""
    last = next(o for o in reversed(out) if o.startswith("\x1b[H"))
    return strip(last).split("\n")


def at(text, nth=0, kind=CLICK):
    """A click on the nth place `text` (or a regex) shows in the last frame."""
    find = text.search if isinstance(text, re.Pattern) else re.compile(re.escape(text)).search

    def aim():
        spots = [(row, m.start()) for row, line in enumerate(frame()) if (m := find(line))]
        assert len(spots) > nth, (text, "\n".join(frame()))
        y, x = spots[nth]
        return Mouse(kind, x + 1, y)
    return aim


def over(text, nth=0):
    """The mouse moved over the nth place `text` shows in the last frame."""
    return at(text, nth, HOVER)


def check(test, then):
    """Run test() when this is read, then give `then`."""
    def run():
        test()
        return then() if callable(then) else then
    return run


def screen(w, h):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)


# ---------------------------------------------------------------- off: nothing changes
console.set_clickable(False)
assert console.hit("row", lambda: None) == "row", "with the mouse off, nothing is marked"
a = App()
a.settings.mouse = False
a.styles()
assert not fake.on and not console.clickable()
a.settings.mouse = True
a.styles()
assert fake.on and console.clickable(), "the setting turns it on (styles() applies it)"
marked = console.hit("row", lambda: None)
assert marked != "row" and console.visible_len(marked) == 3, "the marks take no room"
assert console.pad(marked, 10).count(console.UNHIT) >= 1

# ---------------------------------------------------------------- the main menu
screen(120, 30)
a = App()
a.settings.theme, a.settings.ui_style, a.settings.sidebar_tabs = "mono", "sidebar", "left"
a.settings.art = "off"
menu = Menu(mm.build_items(a), {}, "main")
frames = lambda: sum(o.startswith("\x1b[H") for o in out)
drawn = []
fake.q = [
    over("practice"),                                    # pointing at a section: picks it
    check(lambda: (menu.selected.section == "practice" and menu.on_sections
                   and not drawn.append(frames())) or 1 / 0,
          over("practice")),                             # still there: nothing to redraw
    check(lambda: drawn == [frames()] or 1 / 0, at("practice")),   # a click: enter, its rows
    check(lambda: (menu.selected.section == "practice" and not menu.on_sections) or 1 / 0,
          over("gamemode")),
    check(lambda: (menu.selected.section == "gamemode" and menu.on_sections) or 1 / 0,
          Mouse(CLICK, 100, 25)),                         # nothing there: passed over
    over("2  words"),                                    # a row: selected (its help shows)
    check(lambda: (menu.selected.label == "words" and not menu.on_sections) or 1 / 0,
          Mouse(WHEEL_DOWN, 50, 5)),                      # the wheel: down
    check(lambda: menu.selected.label == "quote" or 1 / 0, Mouse(WHEEL_UP, 50, 5)),
    check(lambda: menu.selected.label == "words" or 1 / 0, at("4  zen")),    # a click: enter
]
got = menu_loop(a, menu, lambda st, m: mm.draw(a, st, m), mm.HINTS, on_back=lambda: "quit")
assert isinstance(got, TestSpec) and got.kind == "zen", got
assert not fake.q

# in the text panel, over the art: the clicks land where the rows are drawn
a.settings.art, a.settings.art_panel, a.settings.theme = "menus", True, "ocean"
menu = Menu(mm.build_items(a), {}, "main")
menu.on_sections = False
fake.q = [over(re.compile("4..zen")),                 # the art shows through the gaps
          check(lambda: menu.selected.label == "zen" or 1 / 0, keys.ESC), keys.ESC]
menu_loop(a, menu, lambda st, m: mm.draw(a, st, m), mm.HINTS, on_back=lambda: "quit")
assert console.panel_shown(), "the panel was on"

# the list style, no border: one click on a row is enter on it
a.settings.art, a.settings.art_panel, a.settings.ui_style = "off", False, "list"
a.settings.border = "off"
menu = Menu(mm.build_items(a), {}, "main")
fake.q = [at("4  zen")]
got = menu_loop(a, menu, lambda st, m: mm.draw(a, st, m), mm.HINTS, on_back=lambda: "quit")
assert isinstance(got, TestSpec) and got.kind == "zen", got

# ---------------------------------------------------------------- settings: pages
screen(140, 34)
a = App()
a.settings.theme, a.settings.ui_style, a.settings.sidebar_tabs = "mono", "sidebar", "left"
a.settings.art = "off"
tree = TreeMenu(sm.build_tree(sm.raw_items(a)), {}, "settings")
assert "other" not in [p.name for p in tree.pages], "the mouse row is filed"
fake.q = [
    at("menus"),                                         # a tab button: into its rows
    check(lambda: (tree.selected.section == "menus" and not tree.on_sections) or 1 / 0,
          at("help ›")),                                 # a page row: opens it
    check(lambda: tree.path() == ["menus", "help"] or 1 / 0, at("layout ›")),   # the column beside
    check(lambda: (tree.path() == ["menus"] and tree.selected.label == "layout ›") or 1 / 0,
          at(re.compile("border {2,}"))),                # a row in the preview of layout
    check(lambda: (tree.path() == ["menus", "layout"] and tree.selected.label == "border")
          or 1 / 0, keys.ESC),                           # opened, on that row; back up
    check(lambda: tree.path() == ["menus"] or 1 / 0, over("mouse ›")),
    check(lambda: tree.selected.label == "mouse ›" or 1 / 0, at("mouse ›")),
    check(lambda: (tree.path() == ["menus", "mouse"] and tree.selected.label == "mouse")
          or 1 / 0, at(re.compile(r"> mouse +on"))),     # the setting, selected: switch it
    check(lambda: (not a.settings.mouse and not fake.on and not console.clickable()) or 1 / 0,
          at("mouse ›")),                                # off now: a click does nothing
    keys.ESC, keys.ESC, keys.ESC,                        # up a page, to the tabs, out
]
menu_loop(a, tree, lambda st, m: sm.draw(a, st, m), sm.HINTS)
assert tree.path() == ["menus"] and not fake.q

# ---------------------------------------------------------------- a dialog over a screen
screen(80, 24)
a = App()
a.settings.theme, a.settings.art = "mono", "off"
a.styles()
under = []
behind = lambda: console.present([console.hit(f"row {k} " * 9, lambda k=k: under.append(k))
                                  for k in range(24)])
fake.q = [Mouse(CLICK, 40, 11),                          # inside the box: not the rows under it
          check(lambda: not under or 1 / 0, Mouse(CLICK, 2, 1)),   # outside it: a row
          check(lambda: under == [0] or 1 / 0, at("No"))]
assert anywhere.resume_dialog(a, behind) is False, "No, clicked"
fake.q = [at("Yes")]
assert anywhere.resume_dialog(a, behind) is True
fake.q = [over("No"), check(lambda: "> No" in "\n".join(frame()) or 1 / 0, keys.ENTER)]
assert anywhere.resume_dialog(a, behind) is False, "pointing at No picks it"

# ---------------------------------------------------------------- never a key in a test
fake.q = [Mouse(CLICK, 1, 1), Mouse(WHEEL_UP, 1, 1), Mouse(MOUSE, 1, 1), "a",
          Mouse(WHEEL_DOWN, 1, 1), "b", Mouse(WHEEL_UP, 1, 1)]
with keys.stamping():
    while fake.q:
        time.sleep(0.001)
    time.sleep(0.02)                                     # all read and timed
    assert keys.read_key(resize=False) == "a", "the test reads past the mouse"
    with keys.over_test():
        assert keys.read_key() == keys.DOWN, "a box over the test (pause, ctrl-o) takes it"
    assert keys.key_ready() and keys.read_key(resize=False) == "b"
    assert not keys.key_ready(), "only the mouse is left"
assert keys.key_ready() is False, "a click left over isn't for the next screen"

# ---------------------------------------------------------------- Linux and macOS
P = _posix
assert repr(P._mouse_event(0, 3, 4)) == "'click'" and P._mouse_event(0, 3, 4).x == 3
assert P._mouse_event(64, 0, 0) == WHEEL_UP and P._mouse_event(65, 0, 0) == WHEEL_DOWN
assert P._mouse_event(0, 0, 0, press=False) == MOUSE, "a release"
assert P._mouse_event(32, 0, 0) == MOUSE and P._mouse_event(2, 0, 0) == MOUSE, "drag, right"
assert P._mouse_event(16, 0, 0) == CLICK, "ctrl-click is a click"
assert P._mouse_event(35, 4, 2) == HOVER, "a move, no button"


def csi(text):
    P._pending[:] = list(text)
    return P._csi()


e = csi("<0;12;5M")
assert e == CLICK and (e.x, e.y) == (11, 4) and not P._pending, "SGR, from 1"
assert csi("<0;12;5m") == MOUSE and csi("<65;1;1M") == WHEEL_DOWN and csi("<35;5;3M").x == 4
e = csi("M" + chr(32) + chr(32 + 10) + chr(32 + 3))
assert e == CLICK and (e.x, e.y) == (9, 2), "the old form"
assert csi("1;5A") == keys.UP and csi("<x;1;1M") == keys.UNKNOWN, "keys still decode"


class Tty:
    def __init__(self):
        self.out = []

    def isatty(self):
        return True

    def write(self, s):
        self.out.append(s)

    def flush(self):
        pass


tty = Tty()
with mock.patch.object(sys, "stdout", tty):
    assert P.mouse(True) and tty.out == [P.MOUSE_ON]
    P.restore()                                          # leaving: the terminal put back
    assert tty.out == [P.MOUSE_ON, P.MOUSE_OFF] and not P._mouse["on"]

# ---------------------------------------------------------------- Windows
if os.name == "nt":
    from minitype.terminal import _windows as W

    def rec(kind, **f):
        r = W._InputRecord()
        r.type = kind
        for k, v in f.items():
            setattr(r.mouse if kind == W.MOUSE_EVENT else r.key, k, v)
        return r

    class K32:
        """The console's input, as kernel32 would show it."""

        def __init__(self, records, mode):
            self.records, self.mode, self.set = list(records), mode, []

        def GetStdHandle(self, n):
            return n

        def PeekConsoleInputW(self, h, buf, size, n):
            for k, r in enumerate(self.records[:size]):
                buf[k] = r
            n._obj.value = min(size, len(self.records))
            return 1

        def ReadConsoleInputW(self, h, buf, size, n):
            del self.records[:size]
            n._obj.value = size
            return 1

        def GetConsoleScreenBufferInfo(self, h, info):
            info._obj.window.Left, info._obj.window.Top = 0, 100   # scrolled down 100 rows
            return 1

        def GetConsoleMode(self, h, mode):
            mode._obj.value = self.mode
            return 1

        def SetConsoleMode(self, h, mode):
            self.set.append(mode)
            self.mode = mode
            return 1

    QUICK = W.ENABLE_QUICK_EDIT_MODE | W.ENABLE_EXTENDED_FLAGS | 0x7
    key_a = rec(W.KEY_EVENT, down=True, char="a", vk=0x41)
    k32 = K32([rec(W.MOUSE_EVENT, x=5, y=107, buttons=W.LEFT_BUTTON, flags=0),
               rec(W.KEY_EVENT, down=False, char="\0", vk=0x41),     # a release: taken
               rec(W.MOUSE_EVENT, x=5, y=107, buttons=0, flags=0),   # the button up
               rec(W.MOUSE_EVENT, x=5, y=107, buttons=0xFF880000, flags=W.MOUSE_WHEELED),
               key_a,
               rec(W.MOUSE_EVENT, x=1, y=101, buttons=W.LEFT_BUTTON, flags=0)], QUICK)
    with mock.patch.object(ctypes, "windll", mock.Mock(kernel32=k32)):
        keys.backend = W
        assert keys.mouse(True) and console.clickable()
        on = k32.set[-1]
        assert on & W.ENABLE_MOUSE_INPUT and not on & W.ENABLE_QUICK_EDIT_MODE \
            and on & W.ENABLE_EXTENDED_FLAGS, hex(on)
        assert W.ready()
        assert len(k32.records) == 2 and k32.records[0] is not None, "stopped at the key"
        first, second = W.read(), W.read()
        assert first == CLICK and (first.x, first.y) == (5, 7), (first, first.y)
        assert second == WHEEL_DOWN
        assert not W._events and len(k32.records) == 2, "the key is left for msvcrt"
        # a double click's second press, and a drag
        W._events.clear()
        W._mouse["held"] = False
        assert W._decode(W._MouseRecord(1, 1, W.LEFT_BUTTON, 0, 0x2)) == [CLICK]
        assert W._decode(W._MouseRecord(2, 1, W.LEFT_BUTTON, 0, W.MOUSE_MOVED)) == []
        assert W._decode(W._MouseRecord(2, 1, 0, 0, 0)) == [], "the release"
        moved = W._decode(W._MouseRecord(3, 1, 0, 0, W.MOUSE_MOVED))
        assert moved == [HOVER] and (moved[0].x, moved[0].y) == (3, 1), "a move, no button"
        # the wheel: a record per notch, or several notches in one, or a
        # touchpad's small turns adding up
        wheel = lambda turn: W._decode(W._MouseRecord(0, 0, (turn & 0xFFFF) << 16, 0,
                                                      W.MOUSE_WHEELED))
        assert wheel(240) == [WHEEL_UP, WHEEL_UP] and wheel(-360) == [WHEEL_DOWN] * 3
        assert wheel(40) == [] and wheel(40) == [] and wheel(40) == [WHEEL_UP]
        keys.restore()                                    # leaving: the mode as it was
        assert k32.set[-1] == QUICK and not W._mouse["on"] and not console.clickable()
    keys.backend = fake

print("ALL OK")
