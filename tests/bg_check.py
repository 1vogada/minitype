import os, re, tempfile, time
HOME = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = HOME
from unittest import mock
from minitype.terminal import console, keys
from minitype.context import App
from minitype.words import books, shlokavitsa as sh
from minitype.engine.runner import TypingTest
from minitype.ui import book_menu as bm

strip = lambda s: re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", s)
console.size = lambda: (100, 40)
frames = []
console.present = lambda lines, focus=None, pinned=(): frames.append(list(lines) + list(pinned))


def feed(seq):
    it = iter(seq)
    return mock.patch.object(keys, "read_key", lambda *a, **k: next(it))


# ---------------------------------------------------------------- transliteration
c = lambda w, s="classic": sh.convert_word(w, s)
assert c("чаша") == "4a6a" and c("щастие") == "6tastie" and c("ябълка") == "qbylka"
assert c("жаба") == "jaba" and c("юмрук") == "iumruk" and c("къща") == "ky6ta"
assert c("Здравей,") == "Zdravei," and c("цвете") == "cvete" and c("Ясен") == "Qsen"
assert c("ЧЕРЕША") == "4ERE6A" and c("ЮГ") == "IUG" and c("Юлия") == "Iuliq"
assert c("чаша", "letters") == "chasha" and c("Щастие", "letters") == "Shtastie"
assert c("ябълка", "letters") == "yabylka" and c("ЖАБА", "letters") == "ZHABA"
assert c("къща", "official") == "kashta" and c("цвете", "official") == "tsvete"
assert c("Здравей", "official") == "Zdravey" and c("ябълка", "official") == "yabalka"
assert c("hello") == "hello" and c("ѝ") == "i"
print("transliteration ok")

# ---------------------------------------------------------------- cleaning keeps cyrillic
words = books.clean("„Здравей, свят!“ — каза тя. Йод, ѝ, ще… **важно** café")
assert words == ['"Здравей,', 'свят!"', "каза", "тя.", "Йод,", "и,", "ще...", "важно", "cafe"], words
assert "й" in books.clean("край")[0], "й must not decompose into и"
assert books.clean("Αθήνα 中文 думи") == ["думи"], "other scripts still dropped"

# ---------------------------------------------------------------- encodings
text = "Това е кратък тест за книга. Чаша, жаба, щастие и ябълка."
assert books.decode(text.encode("utf-8")) == text
assert books.decode(text.encode("cp1251")) == text, "windows-1251 bulgarian file"
assert books.decode("caf\xe9 \x93quoted\x94".encode("latin-1")) == "caf\xe9 “quoted”", "cp1252 still"

# ---------------------------------------------------------------- books in both modes
d = books.folder()
body = " ".join([text] * 30)                    # 330 words
with open(os.path.join(d, "Книга.txt"), "wb") as f:
    f.write(body.encode("cp1251"))
with open(os.path.join(d, "English.txt"), "w", encoding="utf-8") as f:
    f.write("plain english words " * 20)
app = App()
assert books.is_bulgarian("Книга") and not books.is_bulgarian("English")
cyr = books.words(app, "Книга")
assert cyr[:3] == ["Това", "е", "кратък"]
app.settings.book_script = "shlokavitsa"
lat = books.words(app, "Книга")
assert lat[:3] == ["Tova", "e", "kratyk"] and len(lat) == len(cyr), "same word count"
assert "4a6a," in lat and "6tastie" in lat and "qbylka." in lat
assert books.words(app, "English") == books.source_words("English"), "non-bulgarian untouched"
# the converted book is saved as its own txt and reused
p = books.converted_path("Книга", "classic")
assert os.path.isfile(p) and p.startswith(os.path.join(d, "shlokavitsa"))
assert open(p, encoding="utf-8").read().split() == lat
assert books.titles() == ["English", "Книга"], "converted copies aren't listed as books"
books._cache.clear()
with mock.patch.object(sh, "convert", side_effect=AssertionError("should read the saved file")):
    assert books.words(app, "Книга") == lat
# a different style gets its own file
app.settings.shlokavitsa_style = "letters"
assert books.words(app, "Книга")[:6] == ["Tova", "e", "kratyk", "test", "za", "kniga."]
assert os.path.isfile(books.converted_path("Книга", "letters"))
# editing the book makes the conversion redo itself
time.sleep(0.05)
with open(os.path.join(d, "Книга.txt"), "w", encoding="utf-8") as f:
    f.write("Нов текст с щука")
os.utime(os.path.join(d, "Книга.txt"), (time.time() + 5, time.time() + 5))
assert books.words(app, "Книга") == ["Nov", "tekst", "s", "shtuka"]
with open(os.path.join(d, "Книга.txt"), "w", encoding="utf-8") as f:
    f.write(body)
os.utime(os.path.join(d, "Книга.txt"), (time.time() + 10, time.time() + 10))
app.settings.shlokavitsa_style = "classic"

# ---------------------------------------------------------------- bookmark shared by both modes
app.settings.book_page = 50
books.set_page(app, "Книга", 3)
app.settings.book_script = "cyrillic"
s1 = books.page_spec(app, "Книга")
app.settings.book_script = "shlokavitsa"
s2 = books.page_spec(app, "Книга")
assert s1.page == s2.page == 3 and [sh.convert_word(w) for w in s1.words] == list(s2.words)

# ---------------------------------------------------------------- typing a cyrillic page
app.settings.book_script = "cyrillic"
spec = books.page_spec(app, "Книга", 0)
t = TypingTest(app, spec)
for w in spec.words:
    for ch in w:
        t.handle(ch, time.time())
    if not t.finished(time.time()):
        t.handle(" ", time.time())
r = t.result()
assert r.acc == 100 and not r.failed and books.page_of(app, "Книга") == 1

# ---------------------------------------------------------------- the book screen
app.cursors.clear()
with feed([keys.DOWN, keys.ESC]):             # English sorts first; down to Книга
    bm.book_menu(app)
f = strip("\n".join(frames[-1]))
print(f)
assert "Книга" in f and "кирилица" in f and "Това е кратък" in f
# switch to shlokavitsa from the book screen: options row, right
rows = [l for l in f.split("\n")]
# options: filter, bulgarian books, style - down past filter, then right
with feed([keys.TAB, keys.DOWN, keys.RIGHT, keys.SHIFT_TAB, keys.DOWN, keys.ESC]):
    bm.book_menu(app)
f = strip("\n".join(frames[-1]))
print(f)
assert app.settings.book_script == "shlokavitsa"
assert "шльокавица (classic)" in f and "Tova e kratyk" in f
print("ALL OK")
