from ..util import cycle
from ..words.builtin import BUILTIN
from . import storage

TARGETS = [20, 25, 30, 35, 40, 50, 60, 80]
LENGTHS = [10, 15, 20, 30, 50]
START_LETTERS = 6
CAL_SAMPLES = 5         # presses before a key's speed is trusted
SMOOTH = 0.15           # weight of each new press in a key's running speed
MISS_FACTOR = 2.5       # a miss counts as a press this many times too slow
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def _letter_order():
    freq = {}
    for w in BUILTIN:
        for c in w:
            if c in ALPHABET:
                freq[c] = freq.get(c, 0) + 1
    order = sorted(freq, key=lambda c: -freq[c])
    order += [c for c in ALPHABET if c not in freq]
    return "".join(order)


ORDER = _letter_order()   # letters in the order they unlock


class LearnProgress:
    def __init__(self):
        self.config = {
            "target": 35,       # wpm every key must reach before the next letter unlocks
            "letters": 6,       # manual floor for how many letters are in play
            "words": 15,        # words per lesson
            "natural": True,    # real words where enough exist, made-up ones otherwise
            "earned": 0,        # most letters ever unlocked by progress alone
        }
        self.stats = {}         # char -> [smoothed ms per press, presses, misses]
        self.note = ""          # letters unlocked by the lesson that just ended

    # ---------------------------------------------------------------- speed

    def target_ms(self):
        return 12000 / self.config["target"]   # ms per key at the target wpm

    def hit(self, c, ms):
        """Record one press of c. ms=None means it was a miss."""
        if c not in ORDER:
            return
        s = self.stats.setdefault(c, [0.0, 0, 0])
        if ms is None:
            s[2] += 1
            ms = self.target_ms() * MISS_FACTOR
        s[0] = ms if s[1] == 0 else s[0] + SMOOTH * (ms - s[0])
        s[1] += 1

    def conf(self, c):
        """0..1, how close a key is to the target speed. None until it has
        enough presses to trust."""
        s = self.stats.get(c)
        if not s or s[1] < CAL_SAMPLES:
            return None
        return min(1.0, self.target_ms() / s[0])

    def _confident(self, c):
        v = self.conf(c)
        return v is not None and v >= 1.0

    def unlocked(self):
        """How many letters are in play. Grows one at a time once every letter
        so far is at target, and never shrinks from a bad patch."""
        n = max(START_LETTERS, self.config["earned"])
        while n < len(ORDER) and all(self._confident(c) for c in ORDER[:n]):
            n += 1
        self.config["earned"] = n
        return max(self.config["letters"], n)

    def focus_key(self):
        """The weakest unlocked key. Every generated word contains it. Keys with
        no data yet come first, newest first. None once everything is at target."""
        inc = ORDER[:self.unlocked()]

        def rank(i):
            v = self.conf(inc[i])
            return (-1.0 if v is None else v, -i)

        i = min(range(len(inc)), key=rank)
        v = self.conf(inc[i])
        return None if (v is not None and v >= 1.0) else inc[i]

    # ---------------------------------------------------------------- lessons

    def finish(self, n_before):
        n = self.unlocked()
        self.note = ORDER[n_before:n] if n > n_before else ""
        self.save()

    def report(self):
        n = self.unlocked()
        foc = self.focus_key()
        lines = ["", f"{n}/{len(ORDER)} letters   target {self.config['target']} wpm"]
        if self.note:
            lines.append("unlocked " + " ".join(self.note))
        if foc:
            v = self.conf(foc)
            lines.append(f"focus {foc}   " + ("not enough presses yet" if v is None
                                              else f"{v * 100:.0f}% of target"))
        else:
            lines.append("every key at target")
        return lines

    # ---------------------------------------------------------------- options

    def cycle_target(self, step=1):
        self.config["target"] = cycle(TARGETS, self.config["target"], step=step)

    def cycle_length(self, step=1):
        self.config["words"] = cycle(LENGTHS, self.config["words"], step=step)

    def add_letters(self, delta):
        n = self.config["letters"] + delta
        self.config["letters"] = max(START_LETTERS, min(len(ORDER), n))

    def toggle_natural(self):
        self.config["natural"] = not self.config["natural"]

    def reset(self):
        self.stats.clear()
        self.config["earned"] = 0

    # ---------------------------------------------------------------- disk

    def saving(self):
        return storage.enabled()

    def toggle_saving(self):
        storage.toggle(self.to_dict())

    def to_dict(self):
        return {"learn": self.config, "stats": self.stats}

    def save(self):
        storage.write(self.to_dict())

    def load(self):
        d = storage.read()
        if d is None:
            return
        try:
            for k, v in d.get("learn", {}).items():
                if k in self.config and type(v) is type(self.config[k]):
                    self.config[k] = v
            self.stats.clear()
            for c, v in d.get("stats", {}).items():
                if c in ORDER and len(v) == 3:
                    self.stats[c] = [float(v[0]), int(v[1]), int(v[2])]
        except (ValueError, TypeError, AttributeError):
            pass
