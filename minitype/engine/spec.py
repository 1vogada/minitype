from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class TestSpec:
    """What test to run.

    kind:   "words" ends after the words run out, "time" after `amount`
            seconds, "zen" when you press enter.
    source: where the words come from - "words" (word list), "numbers",
            "custom" (uses `words`), "learn", "quote", "code", "slow"
            (your slowest words), "zen" (nothing; you type freely) or
            "book" (one page of a book, in `words`) or "lyrics" (a song's
            lyrics, in `lines`).
    """
    label: str
    kind: str
    amount: int
    source: str = "words"
    words: Optional[Tuple[str, ...]] = None
    book: str = ""      # book mode: which book, and which page (0-based)
    page: int = 0
    # lyrics mode: the song's lines as (seconds or None, text), for the words
    # and the karaoke caret; song_at is (seconds into the song, when that was
    # true) for a song that's already playing (spotify), else (); whole is
    # every line of the song (lines can start partway), for tab to sync again
    lines: Tuple = ()
    song_at: Tuple = ()
    whole: Tuple = ()
