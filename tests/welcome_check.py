"""The welcome screen: the first run (nothing saved) and "reset settings"
bring it up; it says welcome, offers every setup, shows the one you're on
live, and saves the one you pick - keeping your bookmarks."""
import json
import os
import re
import tempfile

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["COLORTERM"] = "truecolor"
from unittest import mock                                   # noqa: E402
from minitype import storage                                # noqa: E402
from minitype.context import App                            # noqa: E402
from minitype.settings import SETUPS, Settings              # noqa: E402
from minitype.terminal import console, keys                 # noqa: E402
from minitype.ui import settings_menu as sm                 # noqa: E402
from minitype.ui.welcome import welcome                     # noqa: E402

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
console.term_size = lambda: (110, 30)
console._last_size = (110, 30)
assert list(SETUPS) == ["clean", "art"], "two setups, clean first"
assert SETUPS["clean"]["art"] == "off" and SETUPS["art"]["art"] != "off"


def drive(app, presses, fn=welcome):
    out = []
    seq = iter(presses)
    with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "write", out.append), \
            mock.patch.object(console, "flush", lambda: None):
        got = fn(app)
    return got, [strip(o) for o in out if o.startswith("\x1b[H")]


# ---------------------------------------------------------------- the first run
app = App()
app.load()
assert app.first_run and app.settings.theme == SETUPS["clean"]["theme"]
generator_settings = app.generator.settings
got, frames = drive(app, [keys.DOWN, keys.ENTER])
assert got == "art" and not app.first_run
assert "welcome to minitype" in frames[0] and "clean" in frames[0] and "art" in frames[0]
assert "up/down choose" in frames[0], "its own hints, whatever the setup says"
for k, v in SETUPS["art"].items():
    assert getattr(app.settings, k) == v, (k, getattr(app.settings, k), v)
assert app.generator.settings is app.settings is generator_settings, "the same settings object"
saved = json.load(open(storage.path(storage.SETTINGS), encoding="utf-8"))
assert saved["art"] == SETUPS["art"]["art"] and saved["theme"] == SETUPS["art"]["theme"]
# saved now: the next start doesn't ask again
again = App()
again.load()
assert not again.first_run and again.settings.theme == SETUPS["art"]["theme"]

# the live preview: on each row the screen is that setup
seen = []
real = App.use_setup
with mock.patch.object(App, "use_setup", lambda self, n: (seen.append(n), real(self, n))):
    drive(App(), [keys.DOWN, keys.UP, "2"])
assert seen[:3] == ["clean", "art", "clean"] and seen[-1] == "art", seen
# esc takes the one you're on
assert drive(App(), [keys.DOWN, keys.ESC])[0] == "art"

# ---------------------------------------------------------------- everything else back to default
app.settings.book_marks = {"1984": 6500}
app.settings.word_amount = 99                       # not in either setup
drive(app, [keys.ENTER])                            # clean
assert app.settings.word_amount == SETUPS["clean"].get("word_amount", Settings().word_amount)
assert app.settings.book_marks == {"1984": 6500}, "bookmarks aren't a setting to reset"

# ---------------------------------------------------------------- reset settings
row = next(it for it in sm.build_items(app) if it.label == "reset settings")
assert row.section == "progress"
_, frames = drive(app, ["n"], fn=lambda a: sm.reset_settings(a))
assert "y/n" in frames[0] and app.settings.theme == SETUPS["clean"]["theme"], "n: nothing happens"
got, frames = drive(app, ["y", keys.DOWN, keys.ENTER], fn=lambda a: sm.reset_settings(a))
assert app.settings.theme == SETUPS["art"]["theme"] and any("welcome to minitype" in f for f in frames)

# ---------------------------------------------------------------- the factory baseline: no welcome
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"
b = App()
b.load()
assert not b.first_run and b.settings.theme == Settings().theme
print("ALL OK")
