"""Favourite quotes: f on a quote's results screen adds / removes it."""
import os, re, tempfile
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.engine.result import TestResult
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.nav import MENU
from minitype.ui import results

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", s)
console.size = lambda: (100, 30)

QUOTE = "Not all those who wander are lost."


def show(app, result, presses):
    frames = []
    seq = iter(presses)
    with mock.patch.object(keys, "read_key", lambda *a, **k: next(seq)), \
            mock.patch.object(console, "present",
                              lambda lines, focus=None, pinned=(), **k: frames.append(
                                  strip("\n".join(list(lines) + list(pinned))))):
        out = results.show_results(app, result)
    return out, frames


def quote_result():
    return TestResult(TestSpec("quote", "words", 0, "quote"), 50, 50, 100, 10, 0, 5,
                      note="proverb", quote=QUOTE)


app = App()
app.settings.art = "off"

# f adds it: star shows, hint is offered, and it is saved to settings.json
out, frames = show(app, quote_result(), ["f", keys.ESC])
assert out is MENU
assert "f favourite" in frames[0] and "★" not in frames[0], frames[0]
assert "★" in frames[1], frames[1]
assert app.settings.fav_quotes == [{"text": QUOTE, "source": "proverb"}]
b = App()
b.load()
assert b.settings.fav_quotes == [{"text": QUOTE, "source": "proverb"}], "persisted"

# f again removes it, and it is never added twice
out, frames = show(app, quote_result(), ["f", "f", keys.ESC])
assert app.settings.fav_quotes == [{"text": QUOTE, "source": "proverb"}], app.settings.fav_quotes
out, frames = show(app, quote_result(), ["f", keys.ESC])
assert app.settings.fav_quotes == [] and "★" not in frames[1]

# a test that is not a quote has no favourite key
plain = TestResult(TestSpec("25 words", "words", 25), 50, 50, 100, 10, 0, 5)
out, frames = show(app, plain, ["f", keys.ESC])
assert app.settings.fav_quotes == [] and "favourite" not in frames[0]

# the quote reaches the result as picked, whatever the punctuation setting
app.settings.punctuation = False
with mock.patch.object(app.quotes, "pick", return_value=(QUOTE, "proverb")):
    t = TypingTest(app, TestSpec("quote", "words", 0, "quote"))
assert t.quote == QUOTE and "." not in t.words[-1]
t.start = 1.0
r = t.result()
assert r.quote == QUOTE, r

# bad favourites in the file are dropped on load
app.settings.apply({"fav_quotes": [{"text": "ok", "source": "x"}, 5, {"source": "no text"}]})
assert app.settings.fav_quotes == [{"text": "ok", "source": "x"}]
print("ALL OK")
