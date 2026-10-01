from .config import BAD_KEYS_TRACKED, KEY_STATES, KEYS

PUNCT_STRIP = ".,;:!?'\"()"
WORD_SMOOTH = 0.4      # weight of the newest timing of a word
MAX_WORDS = 1500       # word timings kept


class SessionStats:
    """Everything remembered about your typing for this session."""

    def __init__(self):
        self.errors = {}      # char -> times missed, drives weak-key bias
        self.missed = {}      # word -> times you submitted it wrong
        self.key_state = {}   # char -> "on" / "off"; absent means auto
        self.history = []     # wpm of completed runs
        self.ghost = []       # (elapsed, chars) samples from the last completed run
        self.word_speed = {}  # word -> [smoothed ms per char, times typed]

    def miss_key(self, c):
        self.errors[c] = self.errors.get(c, 0) + 1

    def miss_word(self, w):
        self.missed[w] = self.missed.get(w, 0) + 1

    def word_time(self, word, ms_per_char):
        """Record how fast a word was typed correctly. Words are stored
        bare and lowercase so punctuation and capitals don't split them."""
        w = word.strip(PUNCT_STRIP).lower()
        if len(w) < 2 or not w.isalpha():
            return
        s = self.word_speed.get(w)
        if s is None:
            self.word_speed[w] = [ms_per_char, 1]
        else:
            s[0] += WORD_SMOOTH * (ms_per_char - s[0])
            s[1] += 1
        if len(self.word_speed) > MAX_WORDS:
            # forget the words seen least
            for k, _ in sorted(self.word_speed.items(), key=lambda kv: kv[1][1])[
                    :len(self.word_speed) - MAX_WORDS]:
                del self.word_speed[k]

    def slowest(self, n):
        """The n words you type slowest, slowest first."""
        ranked = sorted(self.word_speed.items(), key=lambda kv: -kv[1][0])
        return [w for w, _ in ranked[:n]]

    def reset_errors(self):
        self.errors.clear()
        self.missed.clear()

    def best(self):
        return max(self.history) if self.history else None

    def auto_keys(self):
        """Worst keys by error count, ignoring any you've pinned or muted."""
        keys = [(c, n) for c, n in self.errors.items()
                if c.isalnum() and self.key_state.get(c, "auto") == "auto"]
        keys.sort(key=lambda kv: -kv[1])
        return [c for c, _ in keys[:BAD_KEYS_TRACKED]]

    def bad_keys(self):
        """Keys the pool is built from: everything pinned on, plus the automatic
        picks. Muted keys never appear even if you miss them constantly."""
        pinned = [c for c in KEYS if self.key_state.get(c) == "on"]
        return pinned + [c for c in self.auto_keys() if c not in pinned]

    def cycle_key(self, c):
        st = self.key_state.get(c, "auto")
        nxt = KEY_STATES[(KEY_STATES.index(st) + 1) % len(KEY_STATES)]
        if nxt == "auto":
            self.key_state.pop(c, None)
        else:
            self.key_state[c] = nxt

    def ghost_chars(self, elapsed):
        """How far the last run had got by this point."""
        n = 0
        for t, c in self.ghost:
            if t > elapsed:
                break
            n = c
        return n
