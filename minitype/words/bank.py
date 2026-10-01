import json
import urllib.request

from .builtin import BUILTIN
from .themed import THEMED

MONKEYTYPE = ("https://raw.githubusercontent.com/monkeytypegame/monkeytype"
              "/master/frontend/static/")
_MT = MONKEYTYPE + "languages/"

# name -> where it comes from: None (built-in), "themed", or a URL
SOURCES = {
    "built-in": None,
    "online 200": _MT + "english.json",
    "online 1k": _MT + "english_1k.json",
    "online 5k": _MT + "english_5k.json",
    "online 10k": _MT + "english_10k.json",
    "online 25k": _MT + "english_25k.json",
    "online 450k": _MT + "english_450k.json",
    "double letters": _MT + "english_doubleletter.json",
    "misspelled": _MT + "english_commonly_misspelled.json",
    "programming": "themed",
    "left hand": "themed",
    "right hand": "themed",
    "home row": "themed",
}
NAMES = list(SOURCES)
DEFAULT_SOURCE = "online 1k"


def fetch_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)


class WordBank:
    """The active word list. `version` bumps on every load so anything
    derived from the words can tell when its cache is stale."""

    def __init__(self):
        self.words = list(BUILTIN)
        self.source = DEFAULT_SOURCE
        self.note = ""                 # what happened last time we tried to load a list
        self.version = 0
        self._cache = {}               # downloaded lists, so switching back is instant

    @property
    def source_name(self):
        return self.source

    def next_source(self, step=1):
        i = NAMES.index(self.source) if self.source in NAMES else 0
        return NAMES[(i + step) % len(NAMES)]

    def _builtin(self, note):
        self.words = list(BUILTIN)
        self.source = "built-in"
        self.note = note

    def load(self, name, timeout=5):
        """Swap in a word list. Falls back to the built-in list on any failure
        and leaves a note explaining why. Returns True if it worked."""
        self.version += 1
        url = SOURCES.get(name)
        if name not in SOURCES or url is None:
            self._builtin(f"{len(BUILTIN)} words, built-in")
            return name == "built-in"
        if url == "themed":
            self.words = THEMED[name]()
            self.source, self.note = name, f"{len(self.words)} words, {name}"
            return True
        try:
            if url not in self._cache:
                big = name.endswith("k") and name != "online 1k"
                data = fetch_json(url, timeout * 3 if big else timeout)
                words = [w for w in data.get("words", []) if w and " " not in w]
                if len(words) < 50:
                    raise ValueError("list too short")
                self._cache[url] = words
            self.words = self._cache[url]
            self.source, self.note = name, f"{len(self.words)} words, {name}"
            return True
        except Exception as e:
            self._builtin(f"{name} failed ({type(e).__name__}) - using built-in")
            return False
