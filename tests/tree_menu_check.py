"""Cascading menus (minitype/ui/tree_menu.py) and the settings tree
(minitype/ui/settings_tree.py): pages inside pages, opened with enter or
right, left with esc or left; the path shows; search reaches every depth;
nothing is lost."""
import os
import re
import tempfile

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
strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)


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
f = frames(art + [keys.DOWN] * 6 + [keys.ENTER] + [keys.DOWN] * 4 + [keys.ENTER])
# frame k is the screen after the k-th key (frame 0 before any)
crumb = lambda frame: next((l.strip(" │") for l in frame.split("\n") if "settings ›" in l), "")
n = len(art)                                              # frames after reaching art's rows
assert crumb(f[n + 7]).startswith("settings › art › fade") and "top edge" not in crumb(f[n + 7]), f[n + 7]
assert "fade (all pictures)" in f[n + 7] and "top edge" in f[n + 7], "fade's rows, and its pages"
assert crumb(f[n + 12]).startswith("settings › art › fade › top edge") and "fade start top" in f[n + 12], f[n + 12]
assert crumb(f[n + 13]).startswith("settings › art › fade") and "top edge" not in crumb(f[n + 13]), "esc: up to fade"
assert crumb(f[n + 14]) == "" and "art and text" in f[n + 14], "esc esc: back on art's own page"
print("ALL OK")
