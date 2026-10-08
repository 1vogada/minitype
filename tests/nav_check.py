"""Right arrow on a main menu section that opens a screen of its own
(settings, gallery, profile) opens it, like enter; quit stays enter-only."""
import os, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
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
# (quit stays enter-only: columns_check covers it)


# ---------------------------------------------------------------- help box position
import re as _re
from minitype.config import HELP_POSITIONS
from minitype.settings import Settings
assert Settings().help_position == "inline" and HELP_POSITIONS[0] == "inline"
_strip = lambda s: _re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)


def help_frame(where, w=100, h=24):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    a = App()
    a.settings.theme, a.settings.help_position = "forest", where
    out = []
    seq = iter([keys.ESC] * 3)
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        mm.main_menu(a)
    return _strip([o for o in out if o.startswith("\x1b[H")][0].split("\x1b[H", 1)[1]).split("\n")


rows = help_frame("inline")
assert not any("╔" in r for r in rows) and any("┌" in r for r in rows), "inline: the single box"
for where in HELP_POSITIONS[1:]:
    rows = help_frame(where)
    tops = [i for i, r in enumerate(rows) if "╔" in r]
    assert len(tops) == 1 and not any("┌" in r for r in rows), (where, "one double box only")
    t = tops[0]
    bottom = next(i for i, r in enumerate(rows) if "╚" in r)
    col = rows[t].index("╔")
    if where.startswith("top"):
        assert t == 1, (where, t)                        # the first row inside the border
    else:
        hints = next(i for i, r in enumerate(rows) if "arrows" in r)
        assert bottom < hints and bottom >= hints - 3, (where, bottom, hints)
    if where.endswith("right"):
        assert rows[t].rstrip().endswith("╗│"), (where, rows[t])   # against the right edge
    else:
        # beside the menu text, never over it
        for r in range(t, bottom + 1):
            text = rows[r][1:col].rstrip()
            assert len(text) < col, (where, rows[r])
        assert "minitype" in rows[t + 1] or "gamemode" in rows[t + 3] or where.startswith("bottom")
    assert "type as many words" in rows[t + 1], (where, rows[t + 1])
# a corner box is for its frame only: the next screen without help doesn't keep it
console.set_corner("top right", ["X"])
out = []
with mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    console.present(["one"])
    console.present(["two"])
assert "X" in _strip(out[0]) and "X" not in _strip(out[1])
print("ALL OK")
