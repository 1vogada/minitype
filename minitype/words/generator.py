import random

from ..config import PUNCT


class WordGenerator:
    """Builds word sequences for normal tests, applying the bias settings."""

    def __init__(self, settings, stats, bank):
        self.settings = settings
        self.stats = stats
        self.bank = bank
        self._pool_key = None
        self._pool = []

    def bad_pool(self):
        """Words containing at least one bad key, repeated once per bad key they
        hold, so words stacking several of them come up more often. Cached."""
        keys = frozenset(self.stats.bad_keys())
        cache_key = (self.bank.version, keys)
        if cache_key == self._pool_key:
            return self._pool
        pool = []
        for w in self.bank.words:
            hits = sum(1 for c in set(w) if c in keys)
            if hits:
                pool += [w] * min(hits, 3)
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
        return random.choice(self.bank.words)

    def make(self, count, source="words"):
        if source == "numbers":
            return [str(random.randint(0, 10 ** random.randint(1, 5)))
                    for _ in range(count)]
        s = self.settings
        out = []
        sentence = 0
        cap = s.punctuation
        for _ in range(count):
            if s.numbers and random.random() < 0.05:
                out.append(str(random.randint(0, 9999)))
                continue
            w = self.pick()
            if s.punctuation:
                if cap:
                    w = w.capitalize()
                    cap = False
                sentence += 1
                if sentence > 4 and random.random() < 0.3:
                    p = random.choice(PUNCT)
                    w += p
                    if p in ".!?":
                        sentence = 0
                        cap = True
                elif random.random() < 0.04:
                    w = "'" + w + "'"
            out.append(w)
        return out
