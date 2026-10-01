from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class TestSpec:
    """What test to run.

    kind:   "words" ends after the words run out, "time" after `amount`
            seconds, "zen" when you press enter.
    source: where the words come from - "words" (word list), "numbers",
            "custom" (uses `words`), "learn", "quote", "code", "slow"
            (your slowest words) or "zen" (nothing; you type freely).
    """
    label: str
    kind: str
    amount: int
    source: str = "words"
    words: Optional[Tuple[str, ...]] = None
