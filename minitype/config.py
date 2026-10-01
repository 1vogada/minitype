"""Fixed tuning values shared across the app."""

DIFFICULTIES = ["normal", "expert", "master"]
PACES = [0, 40, 60, 80, 100, 120]
PCTS = [20, 40, 60, 80, 100]
BAD_KEYS_TRACKED = 6      # how many of your worst keys feed the pool

PUNCT = ",,,...;:!?"
MAX_EXTRA = 10            # extra chars allowed past the end of a word
VIEW_LINES = 3            # lines of words visible during a test

KEYS = "abcdefghijklmnopqrstuvwxyz0123456789"
# "auto" follows your error counts, "on" always drills, "off" never does.
# Nothing is set either way to start with - every key is auto.
KEY_STATES = ["auto", "on", "off"]
