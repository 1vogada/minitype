"""Typing a number into a number setting, the warning box for a wrong one,
and esc pausing a test."""
import os, re, tempfile, time
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.config import NUMBER_RANGES, FADE_LEVELS
from minitype.settings import Settings
from minitype.terminal import console, keys
from minitype.context import App
from minitype.engine.runner import run_test
from minitype.engine.spec import TestSpec
from minitype.nav import MENU
from minitype.ui import anywhere, settings_menu as sm
from minitype.ui.menu import Menu
from minitype.util import step_number

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)
console.term_size = lambda: (100, 30)

# ---------------------------------------------------------------- stepping
assert step_number(FADE_LEVELS, 30, 1) == 40 and step_number(FADE_LEVELS, 100, 1) == 0
assert step_number(FADE_LEVELS, 35, 1) == 40 and step_number(FADE_LEVELS, 35, -1) == 30
assert step_number(FADE_LEVELS, 105, 1) == 0 and step_number(FADE_LEVELS, -5, -1) == 100

# ---------------------------------------------------------------- saved values
s = Settings()
s.apply({"fade_top": 35, "fade_start": 65, "min_wpm": 77, "effect_speed": 2.5})
assert (s.fade_top, s.fade_start, s.min_wpm, s.effect_speed) == (35, 65, 77, 2.5)
s.apply({"fade_top": 140, "fade_start": 0, "min_wpm": -1, "effect_speed": 9.0})
assert (s.fade_top, s.fade_start, s.min_wpm, s.effect_speed) == (35, 65, 77, 2.5), "out of range"
assert all(isinstance(lo, type(hi)) for lo, hi in NUMBER_RANGES.values())
assert sm.parse_number("fade_top", "35") == 35 and sm.parse_number("fade_top", "101") is None
assert sm.parse_number("fade_top", "3.5") is None, "whole numbers only"
assert sm.parse_number("effect_speed", "1.25") == 1.25 and sm.parse_number("effect_speed", "5") is None

# ---------------------------------------------------------------- typing it
app = App()
items = sm.arrange(sm.build_items(app))
numbered = [it for it in items if getattr(it, "number", None)]
assert {it.number for it in numbered} == set(NUMBER_RANGES), "every number setting takes a typed number"
menu = Menu(items, None, "settings")
menu.cursor = next(i for i, it in enumerate(items) if it.label == "fade top")
warned = []
with mock.patch.object(sm, "warn", lambda a, text, *x, **k: warned.append(text)):
    for k in "35":
        assert sm.number_keys(app, menu, k) == (True, None)
    assert "35" in strip(menu.selected.value()), "shown while typing"
    assert app.settings.fade_top == 50, "not yet"
    sm.number_keys(app, menu, keys.ENTER)
    assert app.settings.fade_top == 35 and not warned
    assert menu.selected.value() == "35%"
    menu.selected.action()
    assert app.settings.fade_top == 40, "right steps on from a typed value"
    # a wrong one: the warning, and the value stays
    for k in "250":
        sm.number_keys(app, menu, k)
    sm.number_keys(app, menu, keys.ENTER)
    assert app.settings.fade_top == 40 and warned and "0 to 100" in warned[0], warned
    # backspace edits, esc cancels
    for k in ["4", "5", keys.BACKSPACE]:
        sm.number_keys(app, menu, k)
    assert sm.ENTRY["text"] == "4"
    assert sm.number_keys(app, menu, keys.ESC) == (True, None)
    assert app.settings.fade_top == 40 and sm.ENTRY["name"] is None
    # an arrow key cancels and is left to the menu
    sm.number_keys(app, menu, "7")
    assert sm.number_keys(app, menu, keys.DOWN) == (False, None) and sm.ENTRY["name"] is None
    # a row that isn't a number: digits go to the search as before
    menu.cursor = next(i for i, it in enumerate(items) if it.label == "difficulty")
    assert sm.number_keys(app, menu, "5") == (False, None)
    # floats
    menu.cursor = next(i for i, it in enumerate(items) if getattr(it, "number", None) == "effect_speed")
    for k in "1.75":
        sm.number_keys(app, menu, k)
    sm.number_keys(app, menu, keys.ENTER)
    assert app.settings.effect_speed == 1.75

# the warning: the pause box over the screen for 1.5 seconds, keys dropped
clock = [0.0]
out, pending = [], ["x", "y"]


def fake_time():
    clock[0] += 0.05
    return clock[0]
with mock.patch.object(time, "time", fake_time), mock.patch.object(time, "sleep", lambda t: None), \
        mock.patch.object(keys, "key_ready", lambda: bool(pending)), \
        mock.patch.object(keys, "read_key", lambda *a, **k: pending.pop()), \
        mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    console.present(["  some menu"])
    start = clock[0]
    anywhere.warn(app, "fade top: 0 to 100, not 250")
    took = clock[0] - start
frames = [strip(f) for f in out if f.startswith("\x1b[H")]
assert any("not 250" in f and "╔" in f and "some menu" in f for f in frames), "box over the screen"
assert "not 250" not in frames[-1], "gone after"
assert 1.5 <= took < 1.7, took
assert not pending, "keys pressed meanwhile are dropped"
assert anywhere.WARN_SECS == 1.5

# ---------------------------------------------------------------- esc pauses
words = tuple("alpha beta gamma delta".split())


def play(app, presses, clock):
    out = []
    seq = iter(presses)

    def read():
        k = next(seq)
        if isinstance(k, float):
            clock[0] += k
            k = next(seq)
        return k
    with mock.patch.object(keys.backend, "read", read), \
            mock.patch.object(keys.backend, "ready", lambda: True), \
            mock.patch.object(keys, "key_ready", lambda: True), \
            mock.patch.object(time, "time", lambda: clock[0]), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        res = run_test(app, TestSpec("c", "words", len(words), "custom", words))
    return res, [strip(f) for f in out if f.startswith("\x1b[H")]


a = App()
assert a.settings.esc_pause
rows = {it.label: it for it in sm.arrange(sm.build_items(a))}
assert rows["pause on esc"].section == "typing screen" and rows["pause on esc"].value() == "on"
# esc mid-test: paused, the minute away doesn't count, enter resumes
res, frames = play(a, list("alpha ") + [keys.ESC, 60.0, keys.ENTER] + list("beta gamma delta"), [1000.0])
assert any("Paused - resume?" in f for f in frames)
assert res not in (None, MENU) and res.elapsed < 30, res
# esc in the box resumes too; No leaves
res, _ = play(a, list("alpha ") + [keys.ESC, keys.ESC] + list("beta gamma delta"), [2000.0])
assert res not in (None, MENU)
res, _ = play(a, list("alpha ") + [keys.ESC, keys.RIGHT, keys.ENTER], [3000.0])
assert res == MENU
# nothing typed yet: esc just leaves
res, frames = play(a, [keys.ESC], [4000.0])
assert res == MENU and not any("Paused" in f for f in frames)
# switched off: esc leaves at once
a.settings.esc_pause = False
res, frames = play(a, list("alp") + [keys.ESC], [5000.0])
assert res == MENU and not any("Paused" in f for f in frames)
print("ALL OK")
