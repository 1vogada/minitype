import json, os, re, tempfile
OLD = tempfile.mkdtemp()
NEW = tempfile.mkdtemp()
os.environ["LOCALAPPDATA"] = OLD
os.environ["MINITYPE_DIR"] = NEW
from unittest import mock
from minitype import storage
from minitype.terminal import console, keys
from minitype.context import App
from minitype.ui import settings_menu as sm, main_menu as mm
from minitype.ui.menu import Menu

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)

# ---------------------------------------------------------------- storage
# without MINITYPE_DIR the files live in the app folder (next to README.md)
saved = os.environ.pop("MINITYPE_DIR")
assert storage.data_dir() == storage.APP_DIR
assert os.path.isfile(os.path.join(storage.APP_DIR, "README.md")), storage.APP_DIR
os.environ["MINITYPE_DIR"] = saved
print("app folder:", storage.APP_DIR)

# settings are written with saving off; save.json is not
app = App()
assert not app.saving()
app.settings.theme = "forest"
app.stats.key_state["q"] = "on"
app.save()
assert os.path.isfile(os.path.join(NEW, "settings.json"))
assert not os.path.isfile(os.path.join(NEW, "save.json"))
on_disk = json.load(open(os.path.join(NEW, "settings.json"), encoding="utf-8"))
assert on_disk["theme"] == "forest" and on_disk["key_state"] == {"q": "on"}
b = App(); b.load()
assert b.settings.theme == "forest" and b.stats.key_state == {"q": "on"}

# settings save on every handled menu key, without leaving the menu
SIZE = [80, 24]
console.size = lambda: tuple(SIZE)
console.present = lambda *a, **k: None
app = App()
seq = iter([keys.DOWN, keys.RIGHT])           # stop on error: off -> letter


def stop_after(*a, **k):
    try:
        return next(seq)
    except StopIteration:
        # read settings.json as it is mid-menu, before esc
        mid = json.load(open(os.path.join(NEW, "settings.json"), encoding="utf-8"))
        assert mid["stop_on_error"] == "letter", mid["stop_on_error"]
        return keys.ESC


with mock.patch.object(keys, "read_key", stop_after):
    sm.settings_menu(app)

# opt-in progress goes to save.json in the same folder; settings stay out of it
app.toggle_saving()
assert os.path.isfile(os.path.join(NEW, "save.json"))
d = json.load(open(os.path.join(NEW, "save.json"), encoding="utf-8"))
assert "settings" not in d and "history" in d
app.toggle_saving()
assert not os.path.isfile(os.path.join(NEW, "save.json"))
assert os.path.isfile(os.path.join(NEW, "settings.json")), "turning saving off keeps settings"

# an old save in %LOCALAPPDATA% is read, moved here on the next save, then removed
for f in ("settings.json", "save.json"):
    p = os.path.join(NEW, f)
    if os.path.exists(p):
        os.remove(p)
os.makedirs(os.path.join(OLD, "minitype"))
old = os.path.join(OLD, "minitype", "save.json")
json.dump({"settings": {"theme": "sunset", "quiet": False}, "key_state": {"z": "off"},
           "pbs": {"30 seconds": {"wpm": 77.0, "acc": 98.0, "t": 1}},
           "learn": {"target": 50}, "history": []}, open(old, "w"))
c = App(); c.load()
assert c.saving(), "old save counts as saving on"
assert c.settings.theme == "sunset" and c.stats.key_state == {"z": "off"}
assert c.history.pbs["30 seconds"]["wpm"] == 77.0 and c.learn.config["target"] == 50
c.save()
assert not os.path.isfile(old), "old copy removed after moving"
assert os.path.isfile(os.path.join(NEW, "save.json"))
assert json.load(open(os.path.join(NEW, "settings.json")))["theme"] == "sunset"
e = App(); e.load()
assert e.history.pbs["30 seconds"]["wpm"] == 77.0 and e.settings.theme == "sunset"

# ---------------------------------------------------------------- section keys
app = App()
items = sm.build_items(app)
for style, tabs in (("list", "off"), ("sidebar", "off"), ("sidebar", "top"),
                    ("sidebar", "left"), ("tabs", "off")):
    m = Menu(items, {}, "s", style=style)
    m.sidebar_tabs = tabs
    assert m.selected.section == "rules"
    m.handle(keys.TAB); assert m.selected.section == "challenges", (style, tabs)
    m.handle("]"); assert m.selected.section == "text"
    m.handle(keys.PGDN); assert m.selected.section == "drills"
    m.handle(keys.SHIFT_TAB); assert m.selected.section == "text"
    m.handle("["); m.handle(keys.PGUP); assert m.selected.section == "rules"
    m.handle(keys.SHIFT_TAB); assert m.selected.section == "progress", "wraps"
    paged = style == "tabs" or tabs != "off"
    m.handle(keys.TAB)                          # back to test
    if tabs == "left":
        m.handle(keys.ENTER)                    # starts on the buttons: into the rows
    for _ in range(9):
        m.handle(keys.DOWN)
    assert (m.selected.section == "rules") == paged, (style, tabs, m.selected.section)
# left/right still change values; on the "edit keys" row (no back) they switch tabs when paged
m = Menu(items, {}, "s", style="sidebar"); m.sidebar_tabs = "left"
before = app.settings.difficulty
m.handle(keys.RIGHT); assert app.settings.difficulty == before, "right on the buttons: into the rows"
m.handle(keys.RIGHT); assert app.settings.difficulty != before and m.selected.section == "rules"
# Tab on results (horizontal) still restarts, it's not a section key there
r = Menu([__import__("minitype.ui.menu", fromlist=["Item"]).Item(keys.TAB, "restart", lambda: "R")],
         horizontal=True)
assert r.handle(keys.TAB) == (True, "R")
# shift-tab decodes from the console
with mock.patch.object(keys.backend, "_getch", side_effect=["\x00", "\x0f"]), \
        mock.patch.object(keys.backend, "ready", lambda: True):
    assert keys.read_key() == keys.SHIFT_TAB


# ---------------------------------------------------------------- what it looks like
def frame(style, tabs, presses, w=90, h=24):
    SIZE[:] = [w, h]
    a = App()
    a.settings.art = "off"     # plain help lines (boxed with art: help_box_check)
    a.settings.ui_style, a.settings.sidebar_tabs = style, tabs
    out = []
    # two esc: in the rows of the two-column layout the first only steps out
    seq = iter(presses + [keys.ESC, keys.ESC])
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "present", lambda lines, focus=None, pinned=(): out.append((lines, focus, pinned))):
        sm.settings_menu(a)
    lines, focus, pinned = out[len(presses)]     # the frame after the last press
    return [strip(l) for l in lines], focus


for tabs in ("top", "left"):
    into_rows = [keys.ENTER] if tabs == "left" else []   # left starts on the buttons
    lines, focus = frame("sidebar", tabs, [keys.TAB] + into_rows + [keys.DOWN, keys.DOWN])
    print(f"===== sidebar tabs {tabs}, 90 wide =====")
    print("\n".join(lines))
    assert lines[focus].lstrip().startswith(">") or "> " in lines[focus] or ">" in lines[focus], lines[focus]
    assert "memory" in lines[focus], lines[focus]
    if tabs == "top":
        assert "challenges" in lines[3] and "memory" in "\n".join(lines)
        assert "difficulty" not in "\n".join(lines), "one section at a time"
        assert "| memory" in lines[focus], "panel level with the selection"
    else:
        assert any(l.startswith("   rules") for l in lines)
        assert "difficulty" not in "\n".join(lines)
        assert "the words disappear" in lines[focus + 1], lines[focus + 1]

# narrow: sidebar+tabs falls back to the tabs layout, never wider than the screen
lines, focus = frame("sidebar", "left", [keys.TAB], w=40, h=14)
print("===== sidebar tabs left, 40 wide =====")
print("\n".join(lines))
assert "funbox" not in lines[focus] and "min speed" in lines[focus]
print("ALL OK")
