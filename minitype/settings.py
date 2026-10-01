from dataclasses import dataclass


@dataclass
class Settings:
    difficulty: str = "normal"   # expert: a wrong word ends it. master: a wrong key ends it.
    punctuation: bool = False
    numbers: bool = False        # sprinkle numbers into normal word tests
    blind: bool = False          # no feedback until the results screen
    weak: bool = False           # bias words toward the keys you keep missing
    weak_pct: int = 50           # how often a biased word is drawn
    bad_words: bool = False      # replay whole words you got wrong
    bad_words_pct: int = 50
    ghost: bool = False          # dim caret replaying your last run
    pace: int = 0                # dim caret moving at a fixed wpm
    quiet: bool = False          # no colour, no banner

    def flags(self):
        """Short labels for every non-default option, for the main menu."""
        flags = []
        if self.difficulty != "normal":
            flags.append(self.difficulty)
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
