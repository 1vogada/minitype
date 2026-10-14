import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
shutil.get_terminal_size = lambda fb=None: os.terminal_size((150, 40))
from minitype.context import App
from minitype.terminal import console

app = App()
s = app.settings
s.art, s.art_behind, s.art_panel = "everywhere", True, True
s.art_style = "revamp"
rows = ["\x1b[38;2;200;100;50m  menu item %d  \x1b[0m" % i for i in range(30)]
for theme in ("ocean", "ember", "candy", "summit"):
    s.theme = theme
    for panel in (False, True):
        s.art_panel = panel
        app.styles()
        out = []
        for use_cache in (False, True):
            console._layered.cache_clear()
            console._last_size = None       # present() clears the screen once per size
            if not use_cache:
                orig = console._layer_cached
                console._layer_cached = lambda r, pic, k, st, col, card, dim: console._layer(
                    r, console._art_cells(pic, k, st, col), card, dim)
            import io
            buf = io.StringIO()
            old, sys.stdout = sys.stdout, buf
            try:
                console.present(rows, scene="menu")
                console.present(rows, scene="menu")     # second frame hits the cache
            finally:
                sys.stdout = old
                if not use_cache:
                    console._layer_cached = orig
            out.append(buf.getvalue())
        assert out[0] == out[1], (theme, panel)
print("cached art rows are identical to the uncached ones")
print("ALL OK")
