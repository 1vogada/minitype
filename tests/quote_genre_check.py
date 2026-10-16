"""Tests for quote themes/genres: settings choice, multi-genre categorization,
length bucket matching, and test runner integration."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp()
os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()

from minitype.config import QUOTE_GENRES, QUOTE_LENGTHS
from minitype.context import App
from minitype.engine.runner import TypingTest
from minitype.engine.spec import TestSpec
from minitype.words.quotes import BUILTIN_QUOTES, QuoteBank, bucket
from minitype.ui import settings_menu as sm


# 1. Config & Settings
assert "all" in QUOTE_GENRES
for required in ("funny", "deep", "philosophical", "movie", "book", "inspirational", "sci-fi"):
    assert required in QUOTE_GENRES, f"missing genre {required}"

app = App()
assert app.settings.quote_genre == "all"
app.settings.quote_genre = "movie"
assert app.settings.quote_genre == "movie"

# apply validation
app.settings.apply({"quote_genre": "sci-fi"})
assert app.settings.quote_genre == "sci-fi"
app.settings.apply({"quote_genre": "invalid_genre_name"})
assert app.settings.quote_genre == "sci-fi", "invalid genre rejected by apply"

# 2. Corpus verification
assert len(BUILTIN_QUOTES) >= 100, f"expected at least 100 quotes, got {len(BUILTIN_QUOTES)}"
all_genres_in_quotes = set()
for q in BUILTIN_QUOTES:
    assert len(q) == 3, f"quote must be a 3-tuple (text, author, genres): {q}"
    text, author, genres = q
    assert isinstance(text, str) and text.strip()
    assert isinstance(author, str) and author.strip()
    assert isinstance(genres, (tuple, list, set)) and len(genres) >= 1
    for g in genres:
        assert g in QUOTE_GENRES, f"unknown genre '{g}' in quote by {author}"
        all_genres_in_quotes.add(g)

# ensure multi-genre quotes exist
multi_group = [q for q in BUILTIN_QUOTES if len(q[2]) > 1]
assert len(multi_group) >= 50, f"expected rich multi-genre quotes, got {len(multi_group)}"

# 3. QuoteBank.pick() behavior
bank = QuoteBank()

# pick returns 2-tuple (text, author), never exposing genre tuple to callers
t, a = bank.pick(genre="all")
assert isinstance(t, str) and isinstance(a, str)

for g in QUOTE_GENRES:
    for length in QUOTE_LENGTHS:
        text, author = bank.pick(length=length, genre=g)
        assert isinstance(text, str) and len(text) > 0
        assert isinstance(author, str) and len(author) > 0

# specific genre picks actually match the genre
for _ in range(30):
    text, author = bank.pick(genre="funny")
    matching = [q for q in BUILTIN_QUOTES if q[0] == text]
    assert matching, f"quote not in pool: {text}"
    assert "funny" in matching[0][2], f"picked quote should be funny: {text}"

for _ in range(30):
    text, author = bank.pick(genre="movie")
    matching = [q for q in BUILTIN_QUOTES if q[0] == text]
    assert matching, f"quote not in pool: {text}"
    assert "movie" in matching[0][2], f"picked quote should be movie: {text}"

# 4. Fallback behavior: online / 2-tuple quotes without genre
class MockOnlineBank(QuoteBank):
    def _pool(self, source):
        return [("Hello world online quote.", "Internet")]

online_bank = MockOnlineBank()
t_on, a_on = online_bank.pick(length="short", genre="movie")
assert t_on == "Hello world online quote." and a_on == "Internet"

# 5. Engine integration: runner respects app.settings.quote_genre
app.settings.quote_genre = "sci-fi"
test = TypingTest(app, TestSpec("quote", "words", 0, "quote"))
assert test.quote, "quote text initialized"
assert test.note, "author initialized"
matching = [q for q in BUILTIN_QUOTES if q[0] == test.quote]
assert matching and "sci-fi" in matching[0][2]

# 6. Settings menu layout
items = sm.build_items(app)
quote_genre_item = next((it for it in items if it.label == "quote genre"), None)
assert quote_genre_item is not None, "quote genre item missing from settings items"
assert quote_genre_item.section == "words", f"expected in words section, got {quote_genre_item.section}"

# Step choice forward and back
before = app.settings.quote_genre
quote_genre_item.action()
assert app.settings.quote_genre != before, "action cycles quote genre"
if quote_genre_item.back:
    quote_genre_item.back()
    assert app.settings.quote_genre == before, "back cycles back quote genre"

print("ALL OK")
