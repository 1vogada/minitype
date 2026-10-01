"""Book mode: type your way through .txt files dropped in the books folder.

Text is cleaned on import so only plain keyboard characters are left:
curly quotes, dashes and accents become their ASCII forms, formatting
marks (markdown-style *, _, #, ~, `, |, =) and divider lines are dropped,
and line breaks become ordinary spaces. Project Gutenberg's licence header
and footer are cut off. Cyrillic letters are kept as they are, so
Bulgarian books work; files in Windows-1251 are read as well as UTF-8.

A Bulgarian book can be typed in Cyrillic, or converted to шльокавица
(see shlokavitsa.py). The converted text is saved as its own .txt in
books/shlokavitsa/, one per style, and reused until the book changes.

A book is split into pages of a fixed number of words. Your place in each
book is kept as a word position, so changing the page size doesn't lose
it. Converting doesn't change the number of words, so the same place
works in Cyrillic and in шльокавица.
"""

import math
import os
import string
import textwrap
import unicodedata

from .. import storage
from ..engine.spec import TestSpec
from . import shlokavitsa

FOLDER = "books"
ALLOWED = set(string.ascii_letters + string.digits + string.punctuation)
FORMATTING = "*_#~`|=<>[]{}^\\"     # stripped from the ends of words
REPLACE = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    "«": '"', "»": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-",
    "…": "...", " ": " ", "­": "",
    "æ": "ae", "Æ": "Ae", "œ": "oe", "Œ": "Oe",
    "ß": "ss", "ø": "o", "Ø": "O", "ł": "l", "Ł": "L",
    "ð": "d", "þ": "th", "Þ": "Th",
}
CYRILLIC_ACCENTED = {"ѝ": "и", "Ѝ": "И", "ѐ": "е", "Ѐ": "Е"}
CYRILLIC_SHARE = 0.3      # share of Cyrillic that makes text count as Bulgarian
SAMPLE_WORDS = 2000       # words looked at to decide that
CONVERTED = "shlokavitsa"   # subfolder for converted copies
GUTENBERG_START = "*** START OF"
GUTENBERG_END = "*** END OF"
PREVIEW_CHARS = 160

_cache = {}     # path -> (mtime, words)


def folder():
    """The books folder, created if it isn't there yet."""
    d = os.path.join(storage.data_dir(), FOLDER)
    os.makedirs(d, exist_ok=True)
    return d


def titles():
    """Book names (file names without .txt), alphabetical."""
    try:
        files = os.listdir(folder())
    except OSError:
        return []
    return sorted((f[:-4] for f in files if f.lower().endswith(".txt")),
                  key=str.lower)


def _read(path):
    with open(path, "rb") as f:
        raw = f.read()
    return decode(raw)


def decode(raw):
    """UTF-8 if it is; otherwise Windows-1251 (older Bulgarian files) or
    Windows-1252 (Western European). Both put letters in bytes 0xC0-0xFF,
    so it goes by proportion: in Bulgarian text most letters are those
    bytes, in Western text most are plain ASCII with a few accents."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    high_letters = sum(1 for b in raw if b >= 0xC0)
    ascii_letters = sum(1 for b in raw if 0x41 <= b <= 0x5A or 0x61 <= b <= 0x7A)
    if high_letters > ascii_letters:
        return raw.decode("cp1251", errors="replace")
    return raw.decode("cp1252", errors="replace")


def strip_gutenberg(text):
    """Keep only the book between Gutenberg's START and END markers."""
    start = text.find(GUTENBERG_START)
    if start != -1:
        line_end = text.find("\n", start)
        text = text[line_end + 1 if line_end != -1 else start:]
    end = text.find(GUTENBERG_END)
    if end != -1:
        text = text[:end]
    return text


def clean_word(w):
    w = w.strip(FORMATTING)
    # a word made only of punctuation is formatting (---, ..., ***), not text
    return w if any(c.isalnum() for c in w) else ""


def _clean_char(c):
    if c in ALLOWED:
        return c
    if c.isspace():
        return " "
    if shlokavitsa.is_cyrillic(c):
        # kept whole: decomposing would turn й into и plus a mark.
        # ѝ and ѐ are just и and е with a stress accent
        return CYRILLIC_ACCENTED.get(c, c) if c.isalpha() else ""
    # Latin accents split off as combining marks, which this filter drops
    return "".join(d for d in unicodedata.normalize("NFKD", c) if d in ALLOWED)


def clean(text):
    """Text to a list of words made only of plain keyboard characters and
    Cyrillic letters."""
    for a, b in REPLACE.items():
        text = text.replace(a, b)
    text = "".join(map(_clean_char, text))
    return [w for w in map(clean_word, text.split()) if w]


def source_words(title):
    """The cleaned words of a book as written, cached until the file
    changes."""
    path = os.path.join(folder(), title + ".txt")
    mtime = os.path.getmtime(path)
    hit = _cache.get(path)
    if hit and hit[0] == mtime:
        return hit[1]
    ws = clean(strip_gutenberg(_read(path)))
    _cache[path] = (mtime, ws)
    return ws


def is_bulgarian(title):
    """A book counts as Cyrillic when a good share of its words are."""
    ws = source_words(title)
    sample = ws[:SAMPLE_WORDS]
    cyr = sum(1 for w in sample if any(shlokavitsa.is_cyrillic(c) for c in w))
    return bool(sample) and cyr >= len(sample) * CYRILLIC_SHARE


def converted_path(title, style):
    return os.path.join(folder(), CONVERTED, f"{title} ({style}).txt")


def converted_words(title, style):
    """The book in шльокавица. Converted once and saved as a .txt, then
    read back from that file until the original book changes."""
    src = os.path.join(folder(), title + ".txt")
    path = converted_path(title, style)
    key = (path, os.path.getmtime(src))
    hit = _cache.get(key)
    if hit:
        return hit
    try:
        if os.path.getmtime(path) >= os.path.getmtime(src):
            with open(path, encoding="utf-8") as f:
                ws = f.read().split()
            _cache[key] = ws
            return ws
    except OSError:
        pass
    ws = shlokavitsa.convert(source_words(title), style)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(textwrap.fill(" ".join(ws), 80))
    except OSError:
        pass                      # still usable, just converted again next time
    _cache[key] = ws
    return ws


def words(app, title):
    """The words to type: the book as written, or in шльокавица when that
    mode is on and the book is Bulgarian."""
    s = app.settings
    if s.book_script == "shlokavitsa" and is_bulgarian(title):
        return converted_words(title, s.shlokavitsa_style)
    return source_words(title)


def script_label(app, title):
    """How a book will be typed, for the book list; "" for non-Cyrillic."""
    if not is_bulgarian(title):
        return ""
    s = app.settings
    return f"шльокавица ({s.shlokavitsa_style})" \
        if s.book_script == "shlokavitsa" else "кирилица"


# ---------------------------------------------------------------- pages

def page_count(n_words, size):
    return max(1, math.ceil(n_words / size))


def page_of(app, title):
    """The page your bookmark is on (0-based)."""
    pos = app.settings.book_marks.get(title, 0)
    return pos // app.settings.book_page


def set_page(app, title, page):
    """Move the bookmark to the start of a page, clamped to the book."""
    size = app.settings.book_page
    last = page_count(len(words(app, title)), size) - 1
    app.settings.book_marks[title] = max(0, min(last, page)) * size


def page_words(app, title, page):
    size = app.settings.book_page
    return words(app, title)[page * size:(page + 1) * size]


def preview(app, title):
    text = " ".join(page_words(app, title, page_of(app, title)))
    return text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else "")


def page_spec(app, title, page=None):
    """A test for one page of a book (the bookmarked page by default)."""
    if page is None:
        page = page_of(app, title)
    total = page_count(len(words(app, title)), app.settings.book_page)
    page = max(0, min(total - 1, page))
    ws = page_words(app, title, page)
    return TestSpec(f"{title}  page {page + 1}/{total}", "words", len(ws),
                    "book", tuple(ws), book=title, page=page)


def finished_page(app, current):
    """After completing a page, the bookmark moves on to the next one."""
    set_page(app, current.book, current.page + 1)


def neighbour(app, current, step):
    """The test for the page `step` pages from `current`, moving the
    bookmark there; None past either end of the book."""
    total = page_count(len(words(app, current.book)), app.settings.book_page)
    page = current.page + step
    if not 0 <= page < total:
        return None
    set_page(app, current.book, page)
    return page_spec(app, current.book, page)
