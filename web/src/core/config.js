// Fixed tuning values, as in minitype/config.py.

export const DIFFICULTIES = ["normal", "expert", "master"];
export const STOP_MODES = ["off", "letter", "word"];
export const PUNCTUATION_MODES = ["off", "on", "forgive"];
export const BACKSPACE_MODES = ["normal", "off", "freedom"];
export const PACES = [0, 40, 60, 80, 100, 120];
export const PCTS = [20, 40, 50, 60, 80, 100];
export const GOALS = [0, 5, 10, 15, 20, 30, 45, 60];
export const MIN_WPMS = [0, 20, 30, 40, 50, 60, 70, 80, 100, 120];
export const MIN_ACCS = [0, 80, 85, 90, 95, 98, 100];
export const MEMORY_SECS = [0, 2, 3, 5, 10];
export const FUNBOXES = ["off", "reversed", "caps", "random case", "mirror", "hacker", "god hacker"];
export const TIMES = [15, 30, 60, 120];
export const WORD_COUNTS = [10, 25, 50, 100];
export const QUOTE_LENGTHS = ["all", "short", "medium", "long"];
export const WORD_LENGTHS = ["any", "short", "short + medium", "medium", "long", "as listed"];
export const QUOTE_SOURCES = ["built-in", "online"];
export const QUOTE_GENRES = ["all", "funny", "deep", "philosophical", "movie", "book", "inspirational", "sci-fi"];
export const CODE_LANGS = ["python", "javascript"];
export const CARETS = ["underline", "block", "line"];
export const WORD_GAPS = ["blank", "dots", "underline"];
export const CORRECTED = ["marked", "normal", "red"];
export const TYPOS = ["off", "below", "replace", "both"];
export const FUN_BOUNCE = ["theme", "off", "gentle", "wild"];
export const FUN_SWITCH = ["theme", "off", "on"];
export const FUN_CARET = ["theme", "off", "pulse", "rainbow"];
export const EFFECT_SPEEDS = [0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0];
export const FLOW_DIRECTIONS = ["forward", "backward"];
export const KEYBOARD_MODES = ["off", "learn", "always"];
export const LOWKEY_MODES = ["off", "minimal"];
export const TAPE_MODES = ["off", "on", "from middle"];
export const WPM_SYSTEMS = ["active", "classic"];
export const THEME_BACKGROUNDS = ["theme", "always", "off"];
export const FX_QUALITY = ["auto", "full", "cheap"];
export const FIRE_MODES = ["off", "streak", "always"];
export const BG_SCENES = ["auto", "off", "synthwave", "mountains", "aurora", "ocean", "city", "blobs"];

export const NUMBER_RANGES = {
  min_wpm: [0, 300], min_acc: [0, 100], memory: [0, 60],
  weak_pct: [0, 100], bad_words_pct: [0, 100], untyped_lighten: [0, 100],
  pace: [0, 300], effect_speed: [0.25, 4.0], daily_goal: [0, 600],
  tilt: [0, 30], fire_wpm: [0, 300],
};

export const BAD_KEYS_TRACKED = 6;
export const PUNCT = ",,,...;:!?";
export const MAX_EXTRA = 10;      // extra chars allowed past the end of a word
export const VIEW_LINES = 3;      // lines of words visible during a test
export const RULE_GRACE = 3.0;    // seconds before min speed / accuracy are enforced
export const KEYS = "abcdefghijklmnopqrstuvwxyz0123456789";
export const KEY_STATES = ["auto", "on", "off"];

export const LAYOUTS = {
  qwerty: ["1234567890-", "qwertyuiop[", "asdfghjkl;'", "zxcvbnm,./"],
  colemak: ["1234567890-", "qwfpgjluy;[", "arstdhneio'", "zxcvbkm,./"],
  dvorak: ["1234567890[", "',.pyfgcrl/", "aoeuidhtns-", ";qjkxbmwvz"],
  qwertz: ["1234567890-", "qwertzuiop[", "asdfghjkl;'", "yxcvbnm,.-"],
  azerty: ["1234567890-", "azertyuiop[", "qsdfghjklm'", "wxcvbn,;:!"],
};

// learn mode: letters in the order they unlock (by frequency in the built-in list)
export const ORDER = "ertaoinslcpudhmgfybwvkxjqz";

// the punctuation a quote's words can be stripped of / skip over
export const QUOTE_PUNCT = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~“”‘’—–…«»";
