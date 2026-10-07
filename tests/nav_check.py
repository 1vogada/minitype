"""Right arrow on a main menu section that opens a screen of its own
(settings, gallery, profile) opens it, like enter - in every layout."""
import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.nav import QUIT
from minitype.ui import main_menu as mm

console.term_size = lambda: (120, 34)


def opened(style, tabs, presses):
    """Which screens the presses opened (and what the menu returned)."""
    seen = []
    a = App()
    a.settings.ui_style, a.settings.sidebar_tabs = style, tabs
    seq = iter(presses + [keys.ESC] * 6)

    def mark(name):
        return lambda app, *x, **k: seen.append(name)
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "present", lambda *x, **k: None), \
            mock.patch.object(mm, "settings_menu", mark("settings")), \
            mock.patch.object(mm, "gallery", mark("gallery")):
        try:
            res = mm.main_menu(a)
        except StopIteration:
            res = None
    return seen, res


# sidebar with the sections down the left: down to the section, right opens it
seen, _ = opened("sidebar", "left", [keys.DOWN, keys.DOWN, keys.RIGHT])
assert seen == ["gallery"], seen
seen, _ = opened("sidebar", "left", [keys.DOWN, keys.DOWN, keys.DOWN, keys.RIGHT])
assert seen == ["settings"], seen
# enter still does it
seen, _ = opened("sidebar", "left", [keys.DOWN, keys.DOWN, keys.DOWN, keys.ENTER])
assert seen == ["settings"], seen
# right on a section with rows (gamemode) steps into the rows, opens nothing
seen, _ = opened("sidebar", "left", [keys.RIGHT])
assert seen == [], seen
# quit: right quits, like enter
_, res = opened("sidebar", "left", [keys.UP, keys.RIGHT])
assert res == QUIT, res
print("ALL OK")
