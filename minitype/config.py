"""Fixed tuning values shared across the app."""

DIFFICULTIES = ["normal", "expert", "master"]
STOP_MODES = ["off", "letter", "word"]
PUNCTUATION_MODES = ["off", "on", "forgive"]
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
QUOTE_GENRES = ["all", "funny", "deep", "philosophical", "movie", "book", "inspirational", "sci-fi"]
CODE_LANGS = ["python", "javascript"]
LYRICS_SOURCES = ["search", "spotify", "liked"]   # lyrics mode: type a song in, what spotify is playing, a liked song
CARETS = ["underline", "block"]
WORD_GAPS = ["blank", "dots", "underline"]   # what's drawn between words
CORRECTED = ["marked", "normal", "red"]     # how a fixed mistake looks
BORDER_STYLES = ["off", "ascii", "line", "rounded", "double", "heavy", "block",
                 "thick"]
ART_FADES = ["edges", "corner", "off"]       # how the art dissolves into the screen
SEE_THROUGH = list(range(0, 101, 10))   # how much art shows through boxes, %
HELP_POSITIONS = ["inline", "top left", "top right", "bottom left", "bottom right"]
# the help box's border: auto (single inline, double in a corner), frame (the
# screen border's), one of the border styles, or off (no border at all)
HELP_BORDERS = ["auto", "frame", "line", "rounded", "double", "heavy", "ascii", "block", "off"]
TEXT_CONTRASTS = ["off", "nudge", "flip"]    # letters over the art: as they are, nudged until
                    # they read, or flipped to the theme's darkest / lightest colour
FADE_LEVELS = list(range(0, 101, 10))          # a fade's strength: 0 none .. 100 no art left
FADE_TOPS = FADE_SIDES = FADE_ROUNDS = FADE_LEVELS
FADE_STARTS = list(range(10, 101, 10))        # how far into the picture a fade reaches, %
FADE_ANGLES = list(range(-60, 61, 15))        # the side fade's tilt, degrees
FADE_CURVES = list(range(0, 11))              # how sharp the fade's curve is (0 straight)
# number settings take any number you type in this range (lowest, highest);
# left / right still step through their lists
NUMBER_RANGES = {
    "min_wpm": (0, 300), "min_acc": (0, 100), "memory": (0, 60),
    "weak_pct": (0, 100), "bad_words_pct": (0, 100), "book_page": (10, 2000),
    "fade_top": (0, 100), "fade_side": (0, 100), "fade_round": (0, 100),
    "fade_start": (1, 100), "fade_start_top": (1, 100), "fade_angle": (-80, 80),
    "fade_curve": (0, 10), "see_through": (0, 100), "text_lighten": (0, 100), "untyped_lighten": (0, 100), "pace": (0, 300), "effect_speed": (0.25, 4.0),
    "daily_goal": (0, 600), "karaoke_offset": (-5000, 5000),
}
ART_SCOPES = ["off", "menus", "everywhere"]  # where the theme's picture shows
ART_STYLES = ["revamp", "blocks", "detailed", "og", "combined", "upscaled"]   # hand-drawn line art,
                    # pixel art, shaded ASCII, the originals, every technique
                    # at once, or the same scenes at braille resolution
# theme: themes that have a background paint it; always: every theme does,
# one made from its colours if it has none (for light terminals); off
THEME_BACKGROUNDS = ["theme", "always", "off"]
ART_COLOURS = ["shaded", "flat"]    # softer shades of the theme, or its colours as they are
TYPOS = ["off", "below", "replace", "both"]  # where the wrong key is shown
# fun modifiers: "theme" follows the theme, the rest force a value
FUN_BOUNCE = ["theme", "off", "gentle", "wild"]
FUN_SWITCH = ["theme", "off", "on"]
FUN_CARET = ["theme", "off", "pulse", "rainbow"]
EFFECT_SPEEDS = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
FLOW_DIRECTIONS = ["forward", "backward"]
KEYBOARD_MODES = ["off", "learn", "always"]
LOWKEY_MODES = ["off", "minimal", "disguised"]
TAPE_MODES = ["off", "on", "from middle"]
LYRICS_TAPE = ["same"] + TAPE_MODES                 # lyrics mode's own tape; same: the tape setting
LYRICS_PUNCT = ["same"] + PUNCTUATION_MODES         # ...and punctuation
LYRICS_CAPITALS = ["same", "on", "forgive", "off"]  # ...and capitals (forgive: shown, shift optional; off: all lowercase)
KARAOKE_OFFSETS = [-2000, -1500, -1000, -750, -500, -250, 0, 250, 500, 750, 1000,
                   1500, 2000]   # ms the karaoke caret is moved on (+) or back (-)
WPM_SYSTEMS = ["active", "classic"]   # active: over the time you typed; classic: the whole clock
LYRICS_LINES = ["new line", "marker", "off"]       # how a song's lines are told apart
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
