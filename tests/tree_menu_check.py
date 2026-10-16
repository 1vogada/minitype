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
assert [it.label for it in m.items] == ["a", "inner", "b", "c"]
assert m.items[1].value() == SUB_MARK and m.items[1].help_text() == "a page in a page"
m.handle(keys.DOWN); m.handle(keys.ENTER)                    # open inner
assert m.selected.label == "i1" and m.path() == ["one", "inner"]
assert [it.label for it in m.items] == ["i1", "deep", "c"], "the other tab keeps its own rows"
m.handle(keys.DOWN); m.handle(keys.RIGHT)                    # right opens a page too
assert m.selected.label == "d1" and m.path() == ["one", "inner", "deep"]
m.handle(keys.ENTER); assert hits == ["d1"], "a setting's own action still runs"
assert m.back_out() and m.selected.label == "deep", "esc: up one page, on the row that opened it"
assert m.back_out() and m.selected.label == "inner" and m.path() == ["one"]
assert not m.back_out(), "at the top: esc leaves (one column)"
m.handle(keys.ENTER); assert m.path() == ["one", "inner"]
m.items[m.cursor].back = None                                # a row with nothing to step back
m.handle(keys.LEFT); assert m.path() == ["one"], "left on such a row goes up too"
m.handle(keys.ENTER)
m.set_query("d2")                                            # search: every depth
assert [it.label for it in m.visible() and [m.items[i] for i in m.visible()]] == ["d2"]
m.set_query("")
assert m.path() == ["one", "inner"], "the search leaves where you were alone"
# two columns: esc goes up a page, then to the tabs, then out
m2 = TreeMenu(pages, {}, "t2", style="sidebar")
m2.sidebar_tabs = "left"
console.term_size = lambda: (120, 30)
assert m2.columns and m2.on_sections
m2.handle(keys.ENTER); assert not m2.on_sections
m2.handle(keys.DOWN); m2.handle(keys.ENTER); assert m2.path() == ["one", "inner"]
assert m2.back_out() and m2.path() == ["one"] and not m2.on_sections
assert m2.back_out() and m2.on_sections
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

# ---------------------------------------------------------------- a page with a switch
state = {"on": False}
flip = lambda: state.update(on=not state["on"])
sw = Item("", "keyboard", flip, lambda: "on" if state["on"] else "off", back=flip)
kb = Page("keyboard", [sw, Item("", "layout", lambda: None, lambda: "qwerty")], "the keyboard", main=sw)
km = TreeMenu([Page("hud", [kb])], {}, "kb")
assert km.selected.label == "keyboard" and km.selected.value() == "off  ›"
km.handle(keys.RIGHT); assert state["on"] and km.path() == ["hud"], "right: the switch, not the page"
km.handle(keys.LEFT); assert not state["on"] and km.path() == ["hud"], "left: the switch back"
km.handle(keys.ENTER); assert km.path() == ["hud", "keyboard"], "enter opens the rest"
assert [it.label for it in km.items] == ["keyboard", "layout"]

# ---------------------------------------------------------------- the settings tree
app = App()
tree = sm.build_tree(sm.raw_items(app))
tops = [p.name for p in tree]
assert tops == ["gameplay", "words", "typing screen", "theme", "effects", "art",
                "interface", "results", "progress", "ui"], tops
assert "other" not in tops, "every row is placed"
raw = sm.raw_items(app)
leaves = [it for p in sm.build_tree(raw) if p.name != "ui" for it in p.leaves()]
assert len(leaves) == len(raw), "every row exactly once (outside the ui tab)"
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


art = [keys.DOWN] * 5 + [keys.RIGHT]                      # the art tab, into its rows
f = frames(art + [keys.DOWN] * 3 + [keys.ENTER] + [keys.DOWN] * 4 + [keys.ENTER])
# frame k is the screen after the k-th key (frame 0 before any)
crumb = lambda frame: next((l.strip(" │") for l in frame.split("\n") if "settings ›" in l), "")
n = len(art)                                              # frames after reaching art's rows
assert crumb(f[n + 4]).startswith("settings › art › fade") and "top edge" not in crumb(f[n + 4]), f[n + 4]
assert "fade (all pictures)" in f[n + 4] and "top edge" in f[n + 4], "fade's rows, and its pages"
assert crumb(f[n + 9]).startswith("settings › art › fade › top edge") and "fade start top" in f[n + 9], f[n + 9]
assert crumb(f[n + 10]).startswith("settings › art › fade") and "top edge" not in crumb(f[n + 10]), "esc: up to fade"
assert crumb(f[n + 11]) == "" and "art and text" in f[n + 11], "esc esc: back on art's own page"
print("ALL OK")
