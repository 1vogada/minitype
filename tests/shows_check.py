"""Which picture the app actually draws, per theme / screen / size."""
import os, sys, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unittest import mock
from minitype.terminal import console, keys, art
from minitype.context import App
from minitype.ui import main_menu as mm
from minitype.ui.gallery import gallery

used = []
orig_row = art.Picture.row


def spy(self, r, start=0):
    used.append(self.height)
    return orig_row(self, r, start)


art.Picture.row = spy


def which(theme, screen, w, h, behind, style="sidebar", tabs="left"):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    a = App()
    a.settings.theme, a.settings.art_behind = theme, behind
    a.settings.ui_style, a.settings.sidebar_tabs = style, tabs
    seq = iter([keys.ESC] * 4)
    used.clear()
    console._art_cells.cache_clear()
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", lambda s: None), \
            mock.patch.object(console, "flush", lambda: None):
        (mm.main_menu if screen == "menu" else gallery)(a)
    heights = set(used)
    new = heights & {28, 22, 16}
    return f"NEW{max(new)}" if new else (f"old({max(heights)})" if heights else "none")


sizes = [(80, 24), (100, 30), (120, 30), (120, 40), (140, 40), (200, 50)]
print(f"{'theme':9} {'screen':7} {'behind':6} " + " ".join(f"{w}x{h}".rjust(8) for w, h in sizes))
for theme in ("ocean", "midnight", "forest", "ember", "default"):
    for screen in ("menu", "gallery"):
        for behind in (False, True):
            print(f"{theme:9} {screen:7} {str(behind):6} " +
                  " ".join(which(theme, screen, w, h, behind).rjust(8) for w, h in sizes))
