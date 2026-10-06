import os, re, tempfile, time
HOME = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = HOME
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.words import books
from minitype.engine.runner import TypingTest
from minitype.ui import book_menu as bm, results as rs, main_menu as mm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
SIZE = [90, 30]
console.size = lambda: tuple(SIZE)
frames = []
console.present = lambda lines, focus=None, pinned=(): frames.append(list(lines) + list(pinned))


def feed(seq):
    it = iter(seq)
    return mock.patch.object(keys, "read_key", lambda *a, **k: next(it))


def last():
    return strip("\n".join(frames[-1]))


# ---------------------------------------------------------------- cleaning
assert books.clean("“Hello,” she said — it’s café time…") == \
    ['"Hello,"', "she", "said", "it's", "cafe", "time..."]
assert books.clean("**bold** _under_ # Heading\n\n---\n***\n=====\nnext") == \
    ["bold", "under", "Heading", "next"]
assert books.clean("naïve Æsop straße øre αβγ 中文 word") == \
    ["naive", "AEsop".replace("AE", "Ae"), "strasse", "ore", "word"]
assert books.clean("line one\r\nline\ttwo three") == ["line", "one", "line", "two", "three"]
g = ("The Project Gutenberg eBook of X\nlicence blah\n"
     "*** START OF THE PROJECT GUTENBERG EBOOK X ***\nCall me Ishmael.\n"
     "*** END OF THE PROJECT GUTENBERG EBOOK X ***\nmore licence")
assert books.clean(books.strip_gutenberg(g)) == ["Call", "me", "Ishmael."]
print("cleaning ok")

# ---------------------------------------------------------------- folder + files
d = books.folder()
assert d == os.path.join(HOME, "books") and os.path.isdir(d)
body = " ".join(f"w{i}" for i in range(120))
with open(os.path.join(d, "Moby.txt"), "w", encoding="utf-8") as f:
    f.write("*** START OF IT ***\n" + body + "\n*** END OF IT ***\nlicence")
with open(os.path.join(d, "old.txt"), "wb") as f:
    f.write("caf\xe9 \x93quoted\x94 words".encode("latin-1"))   # cp1252 bytes
open(os.path.join(d, "empty.txt"), "w").close()
open(os.path.join(d, "notes.md"), "w").close()
assert books.titles() == ["empty", "Moby", "old"], books.titles()
assert books.source_words("old") == ["cafe", '"quoted"', "words"]

# ---------------------------------------------------------------- pages and bookmarks
app = App()
app.settings.book_page = 50
assert books.page_count(len(books.source_words("Moby")), 50) == 3
s = books.page_spec(app, "Moby")
assert s.page == 0 and s.words[0] == "w0" and len(s.words) == 50 and s.label == "Moby  page 1/3"
books.set_page(app, "Moby", 99)
assert books.page_of(app, "Moby") == 2, "clamped to the last page"
assert len(books.page_spec(app, "Moby").words) == 20, "last page is the rest"
books.set_page(app, "Moby", -5)
assert books.page_of(app, "Moby") == 0
# changing page size keeps your place in the text
books.set_page(app, "Moby", 1)               # word 50
app.settings.book_page = 25
assert books.page_of(app, "Moby") == 2 and books.page_spec(app, "Moby").words[0] == "w50"
app.settings.book_page = 50

# ---------------------------------------------------------------- typing a page
books.set_page(app, "Moby", 0)
spec = books.page_spec(app, "Moby")
t = TypingTest(app, spec)
for i, w in enumerate(spec.words):
    for ch in w:
        t.handle(ch, time.time())
    if not t.finished(time.time()):
        t.handle(" ", time.time())
assert t.finished(time.time())
r = t.result()
assert not r.failed and books.page_of(app, "Moby") == 1, "finishing moves the bookmark on"
assert app.history.runs[-1]["mode"] == "book", "one PB for book mode, not one per page"
# pgdn / pgup during a test skip pages
t = TypingTest(app, books.page_spec(app, "Moby"))
nxt = t.handle(keys.PGDN, 0)
assert nxt.page == 2 and books.page_of(app, "Moby") == 2
assert TypingTest(app, nxt).handle(keys.PGDN, 0) is None, "no page after the last"
prev = TypingTest(app, nxt).handle(keys.PGUP, 0)
assert prev.page == 1
assert "pgdn next page" in t.footer()

# ---------------------------------------------------------------- results: next page / restart
books.set_page(app, "Moby", 0)
spec = books.page_spec(app, "Moby")
t = TypingTest(app, spec)
for w in spec.words:
    for ch in w:
        t.handle(ch, time.time())
    if not t.finished(time.time()):
        t.handle(" ", time.time())
r = t.result()
with feed([keys.ENTER]):                      # "next page" is first and selected
    got = rs.show_results(app, r)
assert got.page == 1, got
assert "n next page" in last()
with feed([keys.TAB]):
    got = rs.show_results(app, r)
assert got.page == 0 and books.page_of(app, "Moby") == 0, "restart goes back to that page"
last_page = books.page_spec(app, "Moby", 2)
r.spec = last_page
with feed(["n"]):
    assert rs.show_results(app, r) == "menu" and "last page" in app.notice

# ---------------------------------------------------------------- the book screen
app.cursors.clear()
with feed([keys.ESC]):
    bm.book_menu(app)
f = last()
print(f)
assert "Moby" in f and "page 1/3" in f and "old" in f and "empty" not in f
assert "w0 w1 w2" in f, "preview of the page under the selected book"
# left/right turn a page, pgdn/pgup ten (clamped), g goes to a page, enter reads
books.set_page(app, "Moby", 0)
with feed([keys.DOWN, keys.RIGHT, keys.ESC]):            # Moby is row 2 (after empty-less list: Moby, old)
    bm.book_menu(app)
app.cursors.clear()
books.set_page(app, "Moby", 0)
with feed([keys.RIGHT, keys.RIGHT, keys.LEFT, keys.ENTER]):
    got = bm.book_menu(app)
assert got.book == "Moby" and got.page == 1, got
books.set_page(app, "Moby", 0)
with feed([keys.PGDN, keys.ENTER]):
    assert bm.book_menu(app).page == 2
with feed([keys.PGUP, keys.ENTER]):
    assert bm.book_menu(app).page == 0
with feed(["g", "3", keys.ENTER, keys.ENTER]), mock.patch.object(console, "write"), \
        mock.patch("minitype.ui.prompt.keys.read_key", side_effect=["3", keys.ENTER]):
    pass
with mock.patch("minitype.ui.book_menu.prompt", return_value="3"), feed(["g", keys.ENTER]):
    assert bm.book_menu(app).page == 2
# a new file shows up after refresh
with open(os.path.join(d, "New Book.txt"), "w") as f:
    f.write("fresh words here")
with feed(["r", keys.ESC]):
    bm.book_menu(app)
assert "New Book" in last()
# empty folder message
for name in os.listdir(d):
    os.remove(os.path.join(d, name))
with feed([keys.ESC]):
    bm.book_menu(app)
assert "no books yet" in last() and d in last()
# main menu row
app.cursors.clear()
with feed([keys.ESC]):
    mm.main_menu(app)
assert "book" in last() and "drop .txt files in books/" in last()

# bookmarks persist in settings.json
app.settings.book_marks["Moby"] = 50
app.save()
b = App(); b.load()
assert b.settings.book_marks == app.settings.book_marks and b.settings.book_marks["Moby"] == 50, (b.settings.book_marks, app.settings.book_marks)
b.settings.apply({"book_marks": {"x": -1, "y": "a", "z": 3}})
assert b.settings.book_marks == {"z": 3}
print("ALL OK")
