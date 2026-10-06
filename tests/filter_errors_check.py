import os, string, tempfile, time
HOME = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = HOME
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.words import books
from minitype.engine.runner import TypingTest
from minitype.engine.render import Painter
from minitype.engine.spec import TestSpec
from minitype.ui import book_menu as bm, prompt as pr

# ---------------------------------------------------------------- filter chars
assert books.filter_chars("punct") == string.punctuation
assert books.filter_chars(" Punctuation ") == string.punctuation
assert books.filter_chars(",. ;,") == ",.;", "spaces ignored, duplicates once"
assert books.filter_chars("") == ""
assert books.apply_filter(['said,', '"hi."', "ok", "--"], ',."') == ["said", "hi", "ok", "--"]
assert books.apply_filter(["...", "a"], ".") == ["a"], "a word left empty is dropped"

# ---------------------------------------------------------------- books with a filter
d = books.folder()
with open(os.path.join(d, "Eng.txt"), "w", encoding="utf-8") as f:
    f.write('He said, “hi.” Then: 123 ok! Isn’t it?')
with open(os.path.join(d, "Бг.txt"), "w", encoding="utf-8") as f:
    f.write("Глава 12: чаша, щастие! " * 20)
app = App()
assert books.words(app, "Eng") == ['He', 'said,', '"hi."', 'Then:', '123', 'ok!', "Isn't", 'it?']
app.settings.book_filter = ',."'
assert books.words(app, "Eng") == ['He', 'said', 'hi', 'Then:', '123', 'ok!', "Isn't", 'it?']
app.settings.book_filter = "punct"
assert books.words(app, "Eng") == ['He', 'said', 'hi', 'Then', '123', 'ok', 'Isnt', 'it']
# preview and pages use the filtered words
assert books.preview(app, "Eng").startswith("He said hi Then")
assert books.page_spec(app, "Eng").words[:3] == ("He", "said", "hi")
# shlokavitsa: digits filtered from the book, but the 4 and 6 of the conversion stay
app.settings.book_script = "shlokavitsa"
app.settings.book_filter = "0123456789:,!"
w = books.words(app, "Бг")
assert w[:3] == ["Glava", "4a6a", "6tastie"], w[:6]
# the saved converted book stays the full, unfiltered conversion
app.settings.book_filter = ""
full = books.words(app, "Бг")
assert full[:4] == ["Glava", "12:", "4a6a,", "6tastie!"], full[:4]
saved = open(books.converted_path("Бг", "classic"), encoding="utf-8").read().split()
assert saved == full
app.settings.book_script = "cyrillic"
app.settings.book_filter = "punct"
assert books.words(app, "Бг")[:4] == ["Глава", "12", "чаша", "щастие"]
app.settings.book_filter = ""

# ---------------------------------------------------------------- editing the filter
with mock.patch.object(bm, "prompt", return_value=",.;"):
    bm.edit_book_filter(app)
assert app.settings.book_filter == ",.;" and bm.filter_label(",.;") == ",.;"
with mock.patch.object(bm, "prompt", return_value=None):      # esc
    bm.edit_book_filter(app)
assert app.settings.book_filter == ",.;"
assert bm.filter_label("punct") == "all punctuation" and bm.filter_label("") == "none"
# the prompt starts with the current value and edits it
out = []
seq = iter([keys.BACKSPACE, "!", keys.ENTER])
with mock.patch.object(pr.keys, "read_key", lambda *a, **k: next(seq)), \
        mock.patch.object(console, "write", out.append), mock.patch.object(console, "flush", lambda: None):
    assert pr.prompt("symbols:", ",.;") == ",.!"
assert "symbols: ,.;" in "".join(out)
# and settings remember it
app.save()
b = App(); b.load()
assert b.settings.book_filter == ",.;"


# ---------------------------------------------------------------- keep errors
def typ(t, s):
    for ch in s:
        t.handle(ch, time.time())


def styles_of(t, app):
    st = app.styles()
    p = Painter(st, app.settings, t.words, t.typed, t.wi, (), t.wrong, False, t.error_marks())
    return [(c, s) for s, c, _ in p.word(0)], st


spec = TestSpec("c", "words", 2, "custom", ("cat", "dog"))
app = App()
app.settings.stop_on_error = "letter"
app.settings.corrected = "normal"
# normal: a fixed letter goes back to normal
t = TypingTest(app, spec)
typ(t, "cxa")
cells, st = styles_of(t, app)
assert t.typed[0] == "ca" and cells[1] == ("a", st.ok), cells
t.handle(keys.BACKSPACE, 0)
assert t.typed[0] == "c", "backspace works"
# red: the letter you got wrong stays red after you type it right
app.settings.corrected = "red"
t = TypingTest(app, spec)
typ(t, "cxa")
cells, st = styles_of(t, app)
assert t.typed[0] == "ca"
assert cells[0] == ("c", st.ok) and cells[1] == ("a", st.bad), cells
# keep errors doesn't touch backspace (the backspace setting decides)
t.handle(keys.BACKSPACE, 0)
assert t.typed[0] == "c"
typ(t, "a")
cells, st = styles_of(t, app)
assert cells[1] == ("a", st.bad), "still red after deleting and retyping"
app.settings.backspace = "off"
t.handle(keys.BACKSPACE, 0)
assert t.typed[0] == "ca", "backspace off: no corrections"
app.settings.backspace = "normal"
# an early space in letter mode marks the letter that was due
t = TypingTest(app, spec)
typ(t, "c a")
cells, st = styles_of(t, app)
assert cells[1] == ("a", st.bad)
# blind mode doesn't show it (no feedback until results)
app.settings.blind = True
cells, st = styles_of(t, app)
assert cells[1][1] != st.bad or st.bad == st.ok
app.settings.blind = False
# works without stop on error too: the wrong letter lands red; fixing it
# leaves the right letter red
app.settings.stop_on_error = "off"
t = TypingTest(app, spec)
typ(t, "cx")
t.handle(keys.BACKSPACE, 0)
typ(t, "a")
cells, st = styles_of(t, app)
assert t.typed[0] == "ca" and cells[1] == ("a", st.bad)
# marked (the default): fixed letters in the warn colour, live mistakes red
app.settings.corrected = "marked"
t = TypingTest(app, spec)
typ(t, "cx")
t.handle(keys.BACKSPACE, 0)          # stop on error is off here: fix it by hand
typ(t, "a")
cells, st = styles_of(t, app)
assert cells[1] == ("a", st.warn) and st.warn != st.bad
print("ALL OK")
