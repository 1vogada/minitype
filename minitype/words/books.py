"""Book mode: type your way through .txt files dropped in the books folder.

Text is cleaned on import so only plain keyboard characters are left:
curly quotes, dashes and accents become their ASCII forms, formatting
marks (markdown-style *, _, #, ~, `, |, =) and divider lines are dropped,
and line breaks become ordinary spaces. Project Gutenberg's licence header
and footer are cut off.

A book is split into pages of a fixed number of words. Your place in each
book is kept as a word position, so changing the page size doesn't lose it.
"""

import math
import os
import string
import unicodedata

from .. import storage
from ..engine.spec import TestSpec

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
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


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


def clean(text):
    """Text to a list of words made only of plain keyboard characters."""
    for a, b in REPLACE.items():
        text = text.replace(a, b)
    # accents split off as combining marks, which the ASCII filter drops
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c if c in ALLOWED else " " if c.isspace() else ""
                   for c in text)
    return [w for w in map(clean_word, text.split()) if w]


def words(title):
    """The cleaned words of a book, cached until the file changes."""
    path = os.path.join(folder(), title + ".txt")
    mtime = os.path.getmtime(path)
    hit = _cache.get(path)
    if hit and hit[0] == mtime:
        return hit[1]
    ws = clean(strip_gutenberg(_read(path)))
    _cache[path] = (mtime, ws)
    return ws


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
    last = page_count(len(words(title)), size) - 1
    app.settings.book_marks[title] = max(0, min(last, page)) * size


def page_words(app, title, page):
    size = app.settings.book_page
    return words(title)[page * size:(page + 1) * size]


def preview(app, title):
    text = " ".join(page_words(app, title, page_of(app, title)))
    return text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else "")


def page_spec(app, title, page=None):
    """A test for one page of a book (the bookmarked page by default)."""
    if page is None:
        page = page_of(app, title)
    total = page_count(len(words(title)), app.settings.book_page)
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
    total = page_count(len(words(current.book)), app.settings.book_page)
    page = current.page + step
    if not 0 <= page < total:
        return None
    set_page(app, current.book, page)
    return page_spec(app, current.book, page)
