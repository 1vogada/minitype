"""Print the settings screen with the help box in each position.
python help_look.py W H position [border] [panel] [keys...]"""
import os
import re
import sys
import tempfile

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
sys.path.insert(0, os.environ.get("MT_ROOT", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))))
from unittest import mock                                   # noqa: E402
from minitype.terminal import console, keys                 # noqa: E402
from minitype.context import App                            # noqa: E402
from minitype.ui import settings_menu as sm                 # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)


def look(w, h, where, border="rounded", panel=False, presses=(), extra=None):
    console.term_size = lambda: (w, h)
    console._last_size = (w, h)
    a = App()
    a.settings.theme = "summit"
    a.settings.help_position = where
    a.settings.border = border
    a.settings.art_panel = panel
    for k, v in (extra or {}).items():
        setattr(a.settings, k, v)
    a.styles()
    out = []
    seq = iter(list(presses) + [keys.ESC] * 6 + ["q"] * 3)
    with mock.patch.object(keys, "read_key", lambda *x, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        try:
            sm.settings_menu(a)
        except (StopIteration, SystemExit):
            pass
    frames = [o for o in out if o.startswith("\x1b[H")]
    return strip(frames[len(presses)]).split("\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    names = {"enter": keys.ENTER, "down": keys.DOWN, "up": keys.UP, "tab": keys.TAB,
             "right": keys.RIGHT, "left": keys.LEFT}
    print("\n".join(look(int(a[0]), int(a[1]), a[2], a[3] if len(a) > 3 else "rounded",
                         len(a) > 4 and a[4] == "panel", [names.get(k, k) for k in a[5:]])))
