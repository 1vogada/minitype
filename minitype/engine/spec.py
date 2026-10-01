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
            "book" (one page of a book, in `words`).
    """
    label: str
    kind: str
    amount: int
    source: str = "words"
    words: Optional[Tuple[str, ...]] = None
    book: str = ""      # book mode: which book, and which page (0-based)
    page: int = 0
