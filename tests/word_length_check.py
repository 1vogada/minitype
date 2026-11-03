"""Word length (settings: words › word list › word length). Big word lists
(5k, 10k, 25k) hold mostly long words in their tail, so drawing every word
alike made 10k feel long-words-only (42% 8+ letters, mean 7.2). "any" now
draws a natural mix (short 45 / medium 45 / long 10) from a list like that
and a list that already is one as it is; short / short + medium / medium /
long keep to those lengths; "as listed" is the old draw. Offline: a made-up
list shaped like the 10k one."""
import os
import random
import tempfile
from collections import Counter

os.environ["MINITYPE_DIR"] = tempfile.mkdtemp()
os.environ["MINITYPE_FACTORY"] = "1"
from minitype.config import WORD_LENGTHS                    # noqa: E402
from minitype.context import App                            # noqa: E402
from minitype.settings import Settings                      # noqa: E402
from minitype.ui import settings_menu as sm                 # noqa: E402
from minitype.ui.settings_tree import build_tree            # noqa: E402
from minitype.words import generator as gen                 # noqa: E402

rng = random.Random(7)
letters = "abcdefghijklmnopqrstuvwxyz"


def word(n):
    return "".join(rng.choice(letters) for _ in range(n))


# like online 10k: 13% short, 45% medium, 42% long
TEN_K = list({word(rng.randint(2, 4)) for _ in range(3000)})[:1300] + \
    list({word(rng.randint(5, 7)) for _ in range(6000)})[:4500] + \
    list({word(rng.randint(8, 12)) for _ in range(6000)})[:4200]
# like online 1k: already a natural mix
ONE_K = [word(rng.randint(2, 4)) for _ in range(480)] + [word(rng.randint(5, 7)) for _ in range(460)] + \
    [word(rng.randint(8, 10)) for _ in range(60)]


class Bank:
    def __init__(self, words):
        self.words, self.version = words, 1


class Stats:
    missed = {}

    def __init__(self, bad=()):
        self.bad = list(bad)

    def bad_keys(self):
        return self.bad


def draw(words, mode, n=20000, bad=(), weak=False):
    s = Settings()
    s.word_length, s.weak, s.weak_pct, s.bad_words, s.numbers = mode, weak, 100, False, False
    g = gen.WordGenerator(s, Stats(bad), Bank(words))
    random.seed(1)
    w = g.make(n)
    c = Counter(gen.band(x) for x in w)
    return {b: c[b] * 100 / len(w) for b in gen.BANDS}, w


# ---------------------------------------------------------------- the bands
assert [gen.band(w) for w in ("a", "abcd", "abcde", "abcdefg", "abcdefgh")] == \
    ["short", "short", "medium", "medium", "long"]
assert WORD_LENGTHS[0] == "any" and Settings().word_length == "any"
assert set(gen.WANTED) | {"any", "as listed"} == set(WORD_LENGTHS)

# ---------------------------------------------------------------- 10k: before and after
mix, _ = draw(TEN_K, "as listed")
assert mix["long"] > 38 and mix["short"] < 16, mix            # the old draw: long-heavy
mix, w = draw(TEN_K, "any")
assert 42 < mix["short"] < 48 and 42 < mix["medium"] < 48 and 8 < mix["long"] < 12, mix
assert len(set(w)) > 5000, "still the whole list's variety"
for mode, allowed in gen.WANTED.items():
    mix, _ = draw(TEN_K, mode)
    assert all(mix[b] == 0 for b in gen.BANDS if b not in allowed), (mode, mix)
mix, _ = draw(TEN_K, "short + medium")
assert 45 < mix["short"] < 55, "short + medium: half and half, not by how many there are"

# ---------------------------------------------------------------- a natural list: as it is
mix, _ = draw(ONE_K, "any")
assert 4 < mix["long"] < 8 and 44 < mix["short"] < 52, mix
mix, _ = draw(ONE_K, "long")
assert mix["long"] == 100

# too few words of the lengths asked for: any instead
tiny = ["cat", "dog", "owl", "hen", "pig"] * 2 + ["elephant"]
mix, _ = draw(tiny, "long", 2000)
assert mix["short"] > 50, "one long word doesn't make a test"
assert draw(["a", "b"], "medium", 10)[1]

# the bad keys drill keeps to the lengths too
mix, w = draw(TEN_K, "short", 2000, bad=["q"], weak=True)
assert mix["short"] == 100 and sum("q" in x for x in w) > 1000, "bad-key words, short ones"

# ---------------------------------------------------------------- the settings row
app = App()
tree = build_tree(sm.raw_items(app))


def pages(nodes):
    for n in nodes:
        if getattr(n, "children", None) is not None:
            yield n
            yield from pages(n.children)


page = next(p for p in pages(tree) if p.name == "word list")
labels = [getattr(c, "label", "") for c in page.children]
assert labels[:2] == ["word list", "word length"], labels
row = page.children[1]
assert row.value() == "any"
row.action()
assert app.settings.word_length == "short"
row.back()
row.back()
assert app.settings.word_length == "as listed"
s = Settings()
s.apply({"word_length": "huge"})
assert s.word_length == "any"
s.apply({"word_length": "long"})
assert s.word_length == "long"
print("ALL OK")
