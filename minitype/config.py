"""Fixed tuning values shared across the app."""

DIFFICULTIES = ["normal", "expert", "master"]
STOP_MODES = ["off", "letter", "word"]
PACES = [0, 40, 60, 80, 100, 120]
PCTS = [20, 40, 60, 80, 100]
GOALS = [0, 5, 10, 15, 20, 30, 45, 60]   # daily goal, minutes
CARETS = ["block", "underline"]
KEYBOARD_MODES = ["off", "learn", "always"]
BAD_KEYS_TRACKED = 6      # how many of your worst keys feed the pool

PUNCT = ",,,...;:!?"
MAX_EXTRA = 10            # extra chars allowed past the end of a word
VIEW_LINES = 3            # lines of words visible during a test

KEYS = "abcdefghijklmnopqrstuvwxyz0123456789"
# "auto" follows your error counts, "on" always drills, "off" never does.
# Nothing is set either way to start with - every key is auto.
KEY_STATES = ["auto", "on", "off"]

# rows of the on-screen keyboard, top to bottom
LAYOUTS = {
    "qwerty": ("1234567890-", "qwertyuiop[", "asdfghjkl;'", "zxcvbnm,./"),
    "colemak": ("1234567890-", "qwfpgjluy;[", "arstdhneio'", "zxcvbkm,./"),
    "dvorak": ("1234567890[", "',.pyfgcrl/", "aoeuidhtns-", ";qjkxbmwvz"),
    "qwertz": ("1234567890-", "qwertzuiop[", "asdfghjkl;'", "yxcvbnm,.-"),
    "azerty": ("1234567890-", "azertyuiop[", "qsdfghjklm'", "wxcvbn,;:!"),
}
