import json
import urllib.request

from .builtin import BUILTIN

_MT = "https://raw.githubusercontent.com/monkeytypegame/monkeytype/master/frontend/static/languages/"
SOURCES = [
    ("built-in", None),
    ("online 200", _MT + "english.json"),
    ("online 1k", _MT + "english_1k.json"),
    ("online 5k", _MT + "english_5k.json"),
]
DEFAULT_SOURCE = 2   # the 1k list


class WordBank:
    """The active word list. `version` bumps on every load so anything
    derived from the words can tell when its cache is stale."""

    def __init__(self):
        self.words = list(BUILTIN)
        self.source = DEFAULT_SOURCE   # index into SOURCES
        self.note = ""                 # what happened last time we tried to load a list
        self.version = 0

    @property
    def source_name(self):
        return SOURCES[self.source][0]

    def next_source(self, step=1):
        return (self.source + step) % len(SOURCES)

    def load(self, idx, timeout=5):
        """Swap in a word list. Falls back to the built-in list on any failure
        and leaves a note explaining why. Returns True if the fetch succeeded."""
        self.version += 1
        name, url = SOURCES[idx]
        if url is None:
            self.words = list(BUILTIN)
            self.source, self.note = idx, f"{len(self.words)} words, built-in"
            return True
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                data = json.load(r)
            words = [w for w in data.get("words", []) if w and " " not in w]
            if len(words) < 50:
                raise ValueError("list too short")
            self.words = words
            self.source, self.note = idx, f"{len(self.words)} words, {name}"
            return True
        except Exception as e:
            self.words = list(BUILTIN)
            self.source = 0
            self.note = f"{name} failed ({type(e).__name__}) - using built-in"
            return False
