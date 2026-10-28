"""Cascading menus (minitype/ui/tree_menu.py) and the settings tree
(minitype/ui/settings_tree.py): pages inside pages, opened with enter or
right, left with esc or left; the path shows; search reaches every depth;
nothing is lost."""
import os
import re
import tempfile

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock                                    # noqa: E402
from minitype.terminal import console, keys                  # noqa: E402
from minitype.context import App                             # noqa: E402
from minitype.ui import settings_menu as sm                  # noqa: E402
from minitype.ui.menu import Item                            # noqa: E402
from minitype.ui.tree_menu import SUB_MARK, Page, TreeMenu   # noqa: E402

# ---------------------------------------------------------------- the mechanism
hits = []
row = lambda name: Item("", name, lambda: hits.append(name), lambda: "v", back=lambda: None)
deep = Page("deep", [row("d1"), row("d2")], "the deepest page")
inner = Page("inner", [row("i1"), deep], "a page in a page")
pages = [Page("one", [row("a"), inner, row("b")]), Page("two", [row("c")])]
m = TreeMenu(pages, {}, "t")
assert [it.label for it in m.items] == ["a", "b", f"inner {SUB_MARK}", "c"], "settings first, then pages"
assert m.items[2].value() == "3 settings" and m.items[2].help_text() == "a page in a page"
assert m.items[2].gap and not getattr(m.items[0], "gap", False), "a blank line before the pages"
m.handle(keys.DOWN); m.handle(keys.DOWN)
m.handle(keys.RIGHT)                                         # right opens a page, like enter
assert not hits, "right on a page row changes nothing"
assert m.selected.label == "i1" and m.path() == ["one", "inner"]
assert [it.label for it in m.items] == ["i1", "deep ›", "c"], "the other tab keeps its own rows"
assert m.items[1].value() == "2 settings"
m.handle(keys.DOWN); m.handle(keys.ENTER)
assert m.selected.label == "d1" and m.path() == ["one", "inner", "deep"]
m.handle(keys.ENTER); assert hits == ["d1"], "a setting's own action still runs"
assert m.back_out() and m.selected.label == "deep ›", "esc: up one page, on the row that opened it"
assert m.back_out() and m.selected.label == "inner ›" and m.path() == ["one"]
assert not m.back_out(), "at the top: esc leaves (one column)"
m.handle(keys.ENTER); assert m.path() == ["one", "inner"]
m.items[m.cursor].back = None                                # a row with nothing to step back
m.handle(keys.LEFT); assert m.path() == ["one"], "left on such a row goes up too"
m.handle(keys.ENTER)
m.set_query("d2")                                            # search: every depth
assert [it.label for it in m.visible() and [m.items[i] for i in m.visible()]] == ["d2"]
m.set_query("")
assert m.path() == ["one", "inner", "deep"] and m.selected.label == "d2", \
    "clearing a search opens the pages down to the row you were on"
# two columns: esc goes up a page, then to the tabs, then out
m2 = TreeMenu(pages, {}, "t2", style="sidebar")
m2.sidebar_tabs = "left"
console.term_size = lambda: (120, 30)
assert m2.columns and m2.on_sections
m2.handle(keys.ENTER); assert not m2.on_sections
m2.handle(keys.DOWN); m2.handle(keys.DOWN); m2.handle(keys.ENTER); assert m2.path() == ["one", "inner"]
assert m2.back_out() and m2.path() == ["one"] and not m2.on_sections
m2.handle(keys.RIGHT); assert m2.path() == ["one", "inner"], "right opens it here too"
m2.handle(keys.LEFT); assert m2.path() == ["one"], "left: back up"
m2.handle(keys.LEFT); assert m2.on_sections, "left on a page row at the top: back to the tabs"
m2.handle(keys.ENTER); assert m2.back_out() and m2.on_sections, "esc does the same"
assert not m2.back_out()

# ---------------------------------------------------------------- as deep as you like
leaf = Item("", "bottom", lambda: None, lambda: "v", back=lambda: None)
page = Page("level 50", [leaf])
for k in range(49, 0, -1):
    page = Page(f"level {k}", [Item("", f"row {k}", lambda: None, lambda: "v", back=lambda: None), page])
dm = TreeMenu([page], {}, "deep")
for k in range(1, 50):
    dm.handle(keys.DOWN); dm.handle(keys.ENTER)          # down to the page row, open it
assert dm.selected.label == "bottom" and len(dm.path()) == 50, len(dm.path())
dm.set_query("bottom"); assert [dm.items[i].label for i in dm.visible()] == ["bottom"], "search reaches it"
dm.set_query("")
for k in range(49):
    assert dm.back_out()
assert dm.path() == ["level 1"] and not dm.back_out(), "esc climbs all the way back"
# the path line keeps the page you're on, shortening the start
console.term_size = lambda: (60, 30)
from minitype.terminal.style import Styles
for k in range(30):
    dm.handle(keys.DOWN); dm.handle(keys.ENTER)
line = strip(sm.breadcrumb(Styles("mono"), dm)[0]).strip()
assert line.startswith("settings › … ›") and line.endswith(f"level {len(dm.path())}") \
    and len(dm.path()) > 20 and len(line) <= 60, line

# ---------------------------------------------------------------- the settings tree
app = App()
tree = sm.build_tree(sm.raw_items(app))
tops = [p.name for p in tree]
assert tops == ["in-game", "menus", "data"], tops
assert "other" not in tops, "every row is placed"
assert all(isinstance(c, Page) for p in tree for c in p.children), "the tabs hold only pages"
raw = sm.raw_items(app)
leaves = [it for p in sm.build_tree(raw) for it in p.leaves()]
assert len(leaves) == len(raw) == len({id(it) for it in leaves}), "every row exactly once"
assert len(sm.arrange(sm.build_items(app))) == len(sm.build_items(app)), "arranging twice changes nothing"
# a row nobody filed still shows, in "other"
extra = Item("", "brand new feature", lambda: None, lambda: "on", section="new")
assert sm.build_tree(sm.raw_items(app) + [extra])[-1].name == "other"
# pages are tagged into their rows: #fade finds the fade page's rows
fade_top = next(it for it in sm.build_items(app) if it.label == "fade top")
assert {"art", "fade", "top edge"} <= set(fade_top.tags)

# ---------------------------------------------------------------- on screen


def frames(presses, w=110, h=30):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    a = App()
    a.settings.ui_style, a.settings.sidebar_tabs, a.settings.theme = "sidebar", "left", "mono"
    out = []
    seq = iter(presses + [keys.ESC] * 6)
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        sm.settings_menu(a)
    return [strip(o) for o in out if o.startswith("\x1b[H")]


# the menus tab, into its rows; down to look, open it; down to art, open it
art = [keys.DOWN, keys.RIGHT] + [keys.DOWN] * 3 + [keys.ENTER, keys.DOWN, keys.ENTER]
f = frames(art + [keys.DOWN] * 2 + [keys.ENTER] + [keys.DOWN] * 4 + [keys.ENTER])
# frame k is the screen after the k-th key (frame 0 before any)
crumb = lambda frame: next((l.strip(" │") for l in frame.split("\n") if "settings ›" in l), "")
n = len(art)                                              # frames after reaching art's rows
assert crumb(f[n]).startswith("settings › menus › look › art") and "art and text ›" in f[n], f[n]
assert crumb(f[n + 3]).startswith("settings › menus › look › art › fade"), f[n + 3]
assert "fade (all pictures)" in f[n + 3] and "top edge ›" in f[n + 3], "fade's rows, and its pages"
assert crumb(f[n + 8]).endswith("fade › top edge") and "fade start top" in f[n + 8], f[n + 8]
assert crumb(f[n + 9]).endswith("art › fade"), "esc: up to fade"
assert crumb(f[n + 10]).endswith("look › art") and "art and text ›" in f[n + 10], "esc esc: back on art's page"
# the pages you came through stay beside it, the one you went into marked
into_fade = art + [keys.DOWN] * 2 + [keys.ENTER]
columns = lambda frame: "\n".join(l for l in frame.split("\n") if "settings ›" not in l)
cols = columns(frames(into_fade, w=140)[len(into_fade)])
at = lambda text: max((l.find(text) for l in cols.split("\n")), default=-1)   # its column
assert 0 <= at(">> menus") < at(">> look ›") < at(">> art ›") < at(">> fade ›") \
    < at("> fade (all pictures)"), cols
# narrow: the outermost columns give way, the page you're on keeps its room
cols = columns(frames(into_fade, w=80)[len(into_fade)])
assert ">> fade ›" in cols and "menus" not in cols and "look ›" not in cols, cols
# a page row under the cursor shows what's in it, further right; right steps in
on_test = [keys.RIGHT]                                    # in-game's rows: on "test ›"
cols = columns(frames(on_test, w=130)[1])
assert 0 <= at("> test ›") < at("rules ›") and at("mistakes ›") == at("rules ›"), cols
cols = columns(frames(on_test + [keys.RIGHT], w=130)[2])  # into test: on "rules ›"
assert at(">> test ›") < at("> rules ›") < at("difficulty") and "stop on error  off" in cols, cols

# opened from the main menu, its sections stay on the left; left on the tabs goes back to it
from minitype.ui import main_menu as mm                       # noqa: E402


def main_frames(presses, w=140, h=30):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    a = App()
    a.settings.ui_style, a.settings.sidebar_tabs, a.settings.theme = "sidebar", "left", "mono"
    out = []
    seq = iter(presses + [keys.ESC] * 8 + ["q"] * 3)
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        mm.main_menu(a)
    return [strip(o) for o in out if o.startswith("\x1b[H")]


to_settings = [keys.DOWN] * 3 + [keys.RIGHT]                 # gamemode, practice, gallery, settings
f = main_frames(to_settings + [keys.RIGHT, keys.RIGHT])      # into in-game, then test
cols = columns(f[len(to_settings) + 2])
assert 0 <= at(">> settings") < at(">> in-game") < at(">> test ›") < at("> rules ›"), cols
assert "gamemode" in cols and "profile" in cols, cols
f = main_frames(to_settings + [keys.LEFT])
assert "minitype" in f[len(to_settings) + 1] and "layout ›" not in f[len(to_settings) + 1], \
    "left on the settings tabs: back to the main menu"

# on the main menu the settings section shows the settings' own tabs, not a
# row of rule flags; with the mouse, a click on one opens settings there
on_settings = [keys.DOWN] * 3
f = main_frames(on_settings)[len(on_settings)]
lines = f.splitlines()
row = lambda w: next(i for i, l in enumerate(lines) if re.search(rf"\b{w}\b", l))
assert row("in-game") < row("menus") < row("data"), f
assert lines[row("menus")].index("menus") > lines[row("gamemode")].index("gamemode"), f
a = App()
a.settings.lowercase = True                                  # a rule flag ("lower") used to show
assert "lower" not in main_frames(on_settings)[len(on_settings)]
from minitype.terminal import keynames                       # noqa: E402
out = []
frames = lambda: [strip(o).split("\n") for o in out if o.startswith("\x1b[H")]


def click(word):
    rows = frames()[-1]
    r = next(i for i, l in enumerate(rows) if re.search(rf"\b{word}\s*$", l.rstrip(" │")))
    m = keynames.Mouse(keynames.CLICK)
    m.x, m.y = rows[r].index(word) + 1, r
    return m


seq = iter(on_settings + ["menus", keys.ESC, keys.ESC, keys.ESC, keys.ESC])
read = lambda: (lambda k: click(k) if k == "menus" else k)(next(seq))
a = App()
a.settings.ui_style, a.settings.sidebar_tabs, a.settings.theme = "sidebar", "left", "mono"
console.term_size = lambda: (100, 24)
console._last_size = (100, 24)
with mock.patch.dict(keys._mouse, live=True), \
        mock.patch.object(keys.backend, "mouse", lambda on: on), \
        mock.patch.object(keys.backend, "read", read), \
        mock.patch.object(keys.backend, "ready", lambda: True), \
        mock.patch.object(console, "write", out.append), \
        mock.patch.object(console, "flush", lambda: None):
    mm.main_menu(a)
keys.mouse(False)
opened = "\n".join(frames()[len(on_settings) + 1])
assert "settings" in opened and "> menus" in opened and "layout ›" in opened, opened
print("ALL OK")
