import random

# word lengths (settings: word length): a band per word
SHORT, MEDIUM = 4, 7          # short 1-4 letters, medium 5-7, long 8+
BANDS = ("short", "medium", "long")
# "any": the mix of plain English (the 1k list is 48 / 46 / 6). A list with
# more long words than this (5k, 10k, 25k: their tail is mostly long words)
# draws a band by these shares first, then any word in it; others as listed
NATURAL = {"short": 45, "medium": 45, "long": 10}
WANTED = {"short": ("short",), "short + medium": ("short", "medium"),
          "medium": ("medium",), "long": ("long",)}
MIN_LENGTH_WORDS = 20         # fewer words of the lengths asked for: "any" instead


def band(word):
    n = len(word)
    return "short" if n <= SHORT else "medium" if n <= MEDIUM else "long"


class WordGenerator:
    """Builds word sequences for normal tests, applying the bias settings."""

    def __init__(self, settings, stats, bank):
        self.settings = settings
        self.stats = stats
        self.bank = bank
        self._pool_key = None
        self._pool = []
        self._bands_key = None
        self._bands = {}

    def bands(self):
        """The word list split by length: {band: [words]}. Cached."""
        if self._bands_key != self.bank.version or not self._bands:
            out = {b: [] for b in BANDS}
            for w in self.bank.words:
                out[band(w)].append(w)
            self._bands_key, self._bands = self.bank.version, out
        return self._bands

    def lengths(self):
        """The bands the word length setting allows, or None for no limit
        (any, as listed, or too few words of those lengths)."""
        want = WANTED.get(self.settings.word_length)
        if not want:
            return None
        bands = self.bands()
        return want if sum(len(bands[b]) for b in want) >= MIN_LENGTH_WORDS else None

    def plain(self):
        """A word from the list, by the word length setting."""
        s, words = self.settings, self.bank.words
        if s.word_length == "as listed" or not words:
            return random.choice(words)
        bands = self.bands()
        want = self.lengths()
        if want is None:                        # any: a natural mix, if the list isn't one
            if len(bands["long"]) * 100 <= NATURAL["long"] * len(words):
                return random.choice(words)
            want = BANDS
        want = [b for b in want if bands[b]]    # each band by its natural share
        return random.choice(bands[random.choices(want, [NATURAL[b] for b in want])[0]])

    def bad_pool(self):
        """Words containing at least one bad key, repeated once per bad key they
        hold, so words stacking several of them come up more often; only the
        lengths the word length setting asks for. Cached."""
        keys = frozenset(self.stats.bad_keys())
        want = self.lengths()
        cache_key = (self.bank.version, keys, want)
        if cache_key == self._pool_key:
            return self._pool
        pool = []
        for w in self.bank.words:
            hits = sum(1 for c in set(w) if c in keys)
            if hits:
                pool += [w] * min(hits, 3)
        if want:                                # the lengths asked for, if any of them hold one
            pool = [w for w in pool if band(w) in want] or pool
        self._pool_key, self._pool = cache_key, pool
        return pool

    def missed_pool(self):
        """Words you've submitted wrong, repeated once per time you blew it."""
        pool = []
        for w, n in self.stats.missed.items():
            pool += [w] * min(n, 3)
        return pool

    def pick(self):
        """Roll for a replayed bad word first, then for a bad-key word, and fall
        through to a plain random word when neither hits."""
        s = self.settings
        if s.bad_words and random.random() * 100 < s.bad_words_pct:
            pool = self.missed_pool()
            if pool:
                return random.choice(pool)
        if s.weak and random.random() * 100 < s.weak_pct:
            pool = self.bad_pool()
            if pool:
                return random.choice(pool)
        return self.plain()

    def make(self, count, source="words"):
        if source == "numbers":
            return [str(random.randint(0, 10 ** random.randint(1, 5)))
                    for _ in range(count)]
        s = self.settings
        out = []
        for _ in range(count):
            if s.numbers and random.random() < 0.05:
                out.append(str(random.randint(0, 9999)))
                continue
            out.append(self.pick())
        return out

