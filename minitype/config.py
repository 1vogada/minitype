"""Fixed tuning values shared across the app."""

DIFFICULTIES = ["normal", "expert", "master"]
STOP_MODES = ["off", "letter", "word"]
BACKSPACE_MODES = ["normal", "off", "freedom"]
PACES = [0, 40, 60, 80, 100, 120]
PCTS = [20, 40, 50, 60, 80, 100]
GOALS = [0, 5, 10, 15, 20, 30, 45, 60]   # daily goal, minutes
MIN_WPMS = [0, 20, 30, 40, 50, 60, 70, 80, 100, 120]
MIN_ACCS = [0, 80, 85, 90, 95, 98, 100]
MEMORY_SECS = [0, 2, 3, 5, 10]
FUNBOXES = ["off", "reversed", "caps", "random case", "mirror"]
TIMES = [15, 30, 60, 120]
BOOK_PAGES = [25, 50, 100, 200, 400]     # words per book page
BOOK_SCRIPTS = ["cyrillic", "shlokavitsa"]   # how Bulgarian books are typed
WORD_COUNTS = [10, 25, 50, 100]
QUOTE_LENGTHS = ["all", "short", "medium", "long"]
QUOTE_SOURCES = ["built-in", "online"]
CODE_LANGS = ["python", "javascript"]
CARETS = ["underline", "block"]
WORD_GAPS = ["blank", "dots", "underline"]   # what's drawn between words
CORRECTED = ["marked", "normal", "red"]     # how a fixed mistake looks
TYPOS = ["off", "below", "replace", "both"]  # where the wrong key is shown
# fun modifiers: "theme" follows the theme, the rest force a value
FUN_BOUNCE = ["theme", "off", "gentle", "wild"]
FUN_SWITCH = ["theme", "off", "on"]
FUN_CARET = ["theme", "off", "pulse", "rainbow"]
EFFECT_SPEEDS = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
FLOW_DIRECTIONS = ["forward", "backward"]
KEYBOARD_MODES = ["off", "learn", "always"]
LOWKEY_MODES = ["off", "minimal", "disguised"]
UI_STYLES = ["list", "sidebar", "tabs"]
SIDEBAR_TABS = ["off", "top", "left"]
BAD_KEYS_TRACKED = 6      # how many of your worst keys feed the pool

PUNCT = ",,,...;:!?"
MAX_EXTRA = 10            # extra chars allowed past the end of a word
VIEW_LINES = 3            # lines of words visible during a test
RULE_GRACE = 3.0          # seconds before min speed / accuracy are enforced

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
