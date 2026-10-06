import os, re, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.engine.runner import ZenTest
from minitype.engine.spec import TestSpec
from minitype.ui import main_menu as mm, prompt as pr
from minitype.ui.menu import Item, Menu

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
SIZE = [100, 30]
console.size = lambda: tuple(SIZE)
frames = []
console.present = lambda lines, focus=None, pinned=(): frames.append((list(lines), list(pinned)))


def menu_for(style="sidebar", tabs="left"):
    app = App()
    m = Menu(mm.build_items(app), {}, "main", style=style)
    m.sidebar_tabs = tabs
    return app, m


def draw(app, m):
    lines, focus = m.render(app.styles(), label_width=15)
    return [strip(l) for l in lines], focus


# ---------------------------------------------------------------- two columns
app, m = menu_for()
assert m.columns and m.on_sections, "you start in the left column"
assert m.selected.label == "time" and app.settings.time_amount == 30
lines, focus = draw(app, m)
print("\n".join(lines))
assert lines[0].startswith(" > gamemode ") and lines[focus].startswith(" > gamemode")
assert "test" not in [l.split("|")[0].strip(" >") for l in lines], "renamed"
# on the buttons, left does nothing; right steps into the rows like enter
m.handle(keys.LEFT)
assert m.on_sections and app.settings.time_amount == 30
assert m.nav_hint() == "up/down section   enter/right open"
m.handle(keys.RIGHT)
assert not m.on_sections and app.settings.time_amount == 30, "right enters, changes nothing"
m.back_out()
# up/down on the buttons switch sections
m.handle(keys.DOWN); assert m.selected.section == "practice" and m.on_sections
m.handle(keys.DOWN); assert m.selected.section == "gallery" and m.selected.tab
m.handle(keys.DOWN); assert m.selected.section == "settings" and m.selected.tab
m.handle(keys.DOWN); assert m.selected.section == "profile" and m.selected.tab
m.handle(keys.DOWN); assert m.selected.section == "quit" and m.on_sections
# quit is a button of its own: enter on it quits straight away, right does nothing
assert m.handle(keys.RIGHT) == (True, None) and m.on_sections
assert m.handle(keys.ENTER) == (True, "quit")
m.handle(keys.DOWN); assert m.selected.section == "gamemode", "wraps"
# enter steps into the rows without activating anything
handled, result = m.handle(keys.ENTER)
assert result is None and not m.on_sections and m.selected.label == "time"
# on a row: left/right change the value, shift-enter steps back too
m.handle(keys.RIGHT); assert app.settings.time_amount == 60
m.handle(keys.LEFT); assert app.settings.time_amount == 30
m.handle(keys.RIGHT); m.handle(keys.SHIFT_ENTER); assert app.settings.time_amount == 30
assert not m.on_sections, "left on a row doesn't leave the rows"
assert "esc sections" in m.nav_hint() and "left/right change" in m.nav_hint()
# up/down on the rows move within the section
m.handle(keys.DOWN); m.handle(keys.DOWN); m.handle(keys.DOWN)
assert m.selected.label == "zen"
# a row with no value: left/right do nothing (no section switching)
assert m.handle(keys.RIGHT) == (True, None) and m.handle(keys.LEFT) == (True, None)
assert m.selected.label == "zen" and not m.on_sections
# esc steps back out to the buttons; the row stays selected, dimmed
assert m.back_out() is True and m.on_sections
lines, focus = draw(app, m)
assert lines[focus].startswith(" > gamemode") and "|   4  zen" not in lines[4]
# esc on the buttons is left to the screen (leave the menu)
assert m.back_out() is False
# tab still switches sections from either column
m.handle(keys.TAB); assert m.selected.section == "practice"
# a hotkey from the buttons jumps to its row and focus follows
handled, result = m.handle("2")
assert result.amount == app.settings.word_amount and not m.on_sections

# ---------------------------------------------------------------- other layouts unchanged
for style, tabs in (("list", "off"), ("sidebar", "off"), ("sidebar", "top"), ("tabs", "off")):
    app, m = menu_for(style, tabs)
    assert not m.columns
    m.handle(keys.RIGHT); assert app.settings.time_amount == 60, style
    m.handle(keys.LEFT); assert app.settings.time_amount == 30, style
    m.handle(keys.RIGHT); m.handle(keys.SHIFT_ENTER)
    assert app.settings.time_amount == 30, ("shift-enter steps back everywhere", style)
    assert "left/right change" in m.nav_hint()
# a narrow terminal draws sidebar-left as tabs, so left/right go back to changing values
SIZE[:] = [50, 30]
app, m = menu_for()
assert not m.columns
m.handle(keys.RIGHT); assert app.settings.time_amount == 60, "narrow: right changes"
m.handle(keys.LEFT); assert app.settings.time_amount == 30
SIZE[:] = [100, 30]
# shift-enter on a row with nothing to step back does nothing
m = Menu([Item("", "x", lambda: "went")], {}, "x")
assert m.handle(keys.SHIFT_ENTER) == (True, None)

# ---------------------------------------------------------------- the real screen
app = App()
app.settings.ui_style, app.settings.sidebar_tabs = "sidebar", "left"
seq = iter([keys.ENTER, keys.RIGHT, keys.ESC, keys.DOWN, keys.ESC])
frames.clear()
with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)):
    assert mm.main_menu(app) == "quit", "esc in the rows didn't quit; esc on the buttons did"
assert app.settings.time_amount == 60
texts = [strip("\n".join(l + p)) for l, p in frames]
in_rows = texts[2]            # after enter and right
print(in_rows)
assert "|  >1  time           60s" in in_rows
assert "esc sections" in in_rows and "esc quit" not in in_rows
last = texts[-1]
print(last)
assert " > practice " in last and "up/down section   enter/right open" in last and "esc quit" in last
assert "enter start" not in last and "enter start" in in_rows

# ---------------------------------------------------------------- shift-enter elsewhere
z = ZenTest(app, TestSpec("zen", "zen", 0, "zen"))
for ch in "hi":
    z.handle(ch, 0)
z.handle(keys.SHIFT_ENTER, 0)
assert z.finished(0), "shift-enter finishes zen too"
seq = iter(["a", keys.SHIFT_ENTER])
with mock.patch.object(pr.keys, "read_key", lambda *a, **k: next(seq)), \
        mock.patch.object(console, "write"), mock.patch.object(console, "flush"):
    assert pr.prompt("x") == "a", "shift-enter confirms a prompt"
print("ALL OK")
