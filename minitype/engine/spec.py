from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class TestSpec:
    """What test to run.

    kind:   "words" ends after `amount` words, "time" after `amount` seconds.
    source: "words" (word list), "numbers", "custom" (uses `words`),
            or "learn" (guided lesson).
    """
    label: str
    kind: str
    amount: int
    source: str = "words"
    words: Optional[Tuple[str, ...]] = None
