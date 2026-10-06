"""Print the main menu, as it would show, after some key presses.
python menu_look.py [width height theme style tabs keys...]"""
import os, re, sys, tempfile
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.ui import main_menu as mm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)


def look(w=128, h=24, theme="summit", style="sidebar", tabs="left", presses=(), raw=False,
         behind=os.environ.get("BEHIND") == "1"):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    a = App()
    a.settings.theme, a.settings.ui_style, a.settings.sidebar_tabs = theme, style, tabs
    a.settings.art_behind = behind
    a.styles()
    out = []
    seq = iter(list(presses) + [keys.ESC] * 3 + ["q"])
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        mm.main_menu(a)
    frames = [o for o in out if o.startswith("\x1b[H")]
    f = frames[len(presses)]
    return f if raw else strip(f).split("\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    w, h = int(args[0]) if args else 128, int(args[1]) if len(args) > 1 else 24
    theme = args[2] if len(args) > 2 else "summit"
    names = {"enter": keys.ENTER, "down": keys.DOWN, "up": keys.UP, "tab": keys.TAB}
    presses = [names.get(k, k) for k in args[5:]] or [keys.ENTER]
    print("\n".join(look(w, h, theme, args[3] if len(args) > 3 else "sidebar",
                         args[4] if len(args) > 4 else "left", presses)))
