from dataclasses import asdict, dataclass, fields

from .config import (BACKSPACE_MODES, CARETS, CODE_LANGS, DIFFICULTIES,
                     FUNBOXES, GOALS, KEYBOARD_MODES, LAYOUTS, LOWKEY_MODES,
                     MEMORY_SECS, MIN_ACCS, MIN_WPMS, PACES, QUOTE_LENGTHS,
                     QUOTE_SOURCES, SIDEBAR_TABS, STOP_MODES, THEME_NAMES,
                     UI_STYLES)

# fields whose value must be one of a fixed set
CHOICES = {
    "difficulty": DIFFICULTIES,
    "stop_on_error": STOP_MODES,
    "backspace": BACKSPACE_MODES,
    "min_wpm": MIN_WPMS,
    "min_acc": MIN_ACCS,
    "funbox": FUNBOXES,
    "memory": MEMORY_SECS,
    "quote_length": QUOTE_LENGTHS,
    "quote_source": QUOTE_SOURCES,
    "code_lang": CODE_LANGS,
    "pace": PACES,
    "caret": CARETS,
    "keyboard": KEYBOARD_MODES,
    "layout": list(LAYOUTS),
    "theme": THEME_NAMES,
    "lowkey": LOWKEY_MODES,
    "ui_style": UI_STYLES,
    "sidebar_tabs": SIDEBAR_TABS,
    "daily_goal": GOALS,
}


@dataclass
class Settings:
    # ---- the test
    difficulty: str = "normal"   # expert: a wrong word ends it. master: a wrong key ends it.
    stop_on_error: str = "off"   # letter: wrong keys don't move the cursor. word: can't leave a wrong word
    backspace: str = "normal"    # off: no corrections at all. freedom: back into correct words too
    punctuation: bool = False
    numbers: bool = False        # sprinkle numbers into normal word tests
    blind: bool = False          # no feedback until the results screen
    time_amount: int = 30        # seconds, for the time mode
    word_amount: int = 25        # words, for the words and numbers modes

    # ---- challenges
    min_wpm: int = 0             # fail when live speed drops below this
    min_acc: int = 0             # fail when accuracy drops below this
    funbox: str = "off"          # reversed / caps / random case / mirror
    memory: int = 0              # hide the words this many seconds in

    # ---- practising weaknesses
    weak: bool = False           # bias words toward the keys you keep missing
    weak_pct: int = 50           # how often a biased word is drawn
    bad_words: bool = False      # replay whole words you got wrong
    bad_words_pct: int = 50

    # ---- text sources
    word_source: str = "online 1k"
    quote_length: str = "all"
    quote_source: str = "built-in"
    code_lang: str = "python"

    # ---- look and feel
    theme: str = "default"
    lowkey: str = "off"          # minimal: just the words. disguised: looks like a plain prompt
    ui_style: str = "list"       # how menus are laid out
    sidebar_tabs: str = "off"    # sidebar style: tab bar on top, or section buttons on the left
    tape: bool = False           # one scrolling line instead of a block of lines
    caret: str = "block"
    show_spaces: bool = False    # draw spaces between words as dots
    keyboard: str = "learn"      # on-screen keyboard: off, in learn mode, or always
    layout: str = "qwerty"       # for the on-screen keyboard
    ghost: bool = False          # dim caret replaying your last run
    pace: int = 0                # dim caret moving at a fixed wpm
    sound: bool = False          # bell on a wrong key
    hints: bool = True           # key hints at the bottom of each screen

    # ---- header during a test
    show_timer: bool = True
    show_progress: bool = True
    show_wpm: bool = True
    show_combo: bool = True

    # ---- results screen sections
    res_chart: bool = True
    res_heatmap: bool = True
    res_pb: bool = True
    res_worst_keys: bool = True
    res_session_keys: bool = True
    res_bad_words: bool = True
    res_history: bool = True

    # ---- progress
    daily_goal: int = 0          # minutes of typing a day, 0 for none

    @property
    def quiet(self):
        return self.theme == "mono" or self.lowkey == "disguised"

    def flags(self):
        """Short labels for every non-default rule, for the main menu."""
        flags = []
        if self.difficulty != "normal":
            flags.append(self.difficulty)
        if self.stop_on_error != "off":
            flags.append(f"stop-{self.stop_on_error}")
        if self.backspace != "normal":
            flags.append("no-bksp" if self.backspace == "off" else "freedom")
        for on, name in ((self.punctuation, "punct"), (self.numbers, "num"),
                         (self.blind, "blind"), (self.ghost, "ghost"),
                         (self.tape, "tape")):
            if on:
                flags.append(name)
        if self.funbox != "off":
            flags.append(self.funbox)
        if self.memory:
            flags.append(f"memory{self.memory}s")
        if self.min_wpm:
            flags.append(f"min{self.min_wpm}wpm")
        if self.min_acc:
            flags.append(f"min{self.min_acc}%")
        if self.weak:
            flags.append(f"keys{self.weak_pct}%")
        if self.bad_words:
            flags.append(f"words{self.bad_words_pct}%")
        if self.pace:
            flags.append(f"pace{self.pace}")
        return flags

    def to_dict(self):
        return asdict(self)

    def apply(self, d):
        """Take saved values, skipping any of the wrong type or out of range."""
        if not isinstance(d, dict):
            return
        if d.get("quiet") is True and "theme" not in d:
            self.theme = "mono"          # from before themes existed
        for f in fields(self):
            v = d.get(f.name)
            if type(v) is not type(getattr(self, f.name)):
                continue
            if f.name in CHOICES and v not in CHOICES[f.name]:
                continue
            if f.name in ("time_amount", "word_amount") and not 0 < v <= 3600:
                continue
            setattr(self, f.name, v)
