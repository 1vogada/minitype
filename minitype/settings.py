from dataclasses import asdict, dataclass, fields

from .config import (CARETS, DIFFICULTIES, GOALS, KEYBOARD_MODES, LAYOUTS,
                     PACES, STOP_MODES)

# fields whose value must be one of a fixed set
CHOICES = {
    "difficulty": DIFFICULTIES,
    "stop_on_error": STOP_MODES,
    "pace": PACES,
    "caret": CARETS,
    "keyboard": KEYBOARD_MODES,
    "layout": list(LAYOUTS),
    "daily_goal": GOALS,
}


@dataclass
class Settings:
    difficulty: str = "normal"   # expert: a wrong word ends it. master: a wrong key ends it.
    stop_on_error: str = "off"   # letter: wrong keys don't move the cursor. word: can't leave a wrong word
    punctuation: bool = False
    numbers: bool = False        # sprinkle numbers into normal word tests
    blind: bool = False          # no feedback until the results screen
    weak: bool = False           # bias words toward the keys you keep missing
    weak_pct: int = 50           # how often a biased word is drawn
    bad_words: bool = False      # replay whole words you got wrong
    bad_words_pct: int = 50
    ghost: bool = False          # dim caret replaying your last run
    pace: int = 0                # dim caret moving at a fixed wpm
    caret: str = "block"
    show_spaces: bool = False    # draw spaces between words as dots
    keyboard: str = "learn"      # on-screen keyboard: off, in learn mode, or always
    layout: str = "qwerty"       # for the on-screen keyboard
    sound: bool = False          # bell on a wrong key
    daily_goal: int = 0          # minutes of typing a day, 0 for none
    quiet: bool = False          # no colour, no banner

    def flags(self):
        """Short labels for every non-default option, for the main menu."""
        flags = []
        if self.difficulty != "normal":
            flags.append(self.difficulty)
        if self.stop_on_error != "off":
            flags.append(f"stop-{self.stop_on_error}")
        for on, name in ((self.punctuation, "punct"), (self.numbers, "num"),
                         (self.blind, "blind"), (self.ghost, "ghost")):
            if on:
                flags.append(name)
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
        for f in fields(self):
            v = d.get(f.name)
            if type(v) is not type(getattr(self, f.name)):
                continue
            if f.name in CHOICES and v not in CHOICES[f.name]:
                continue
            setattr(self, f.name, v)
