from dataclasses import dataclass, field

from .spec import TestSpec


@dataclass
class TestResult:
    spec: TestSpec
    wpm: float
    raw: float
    acc: float
    elapsed: float
    errors: int
    best_combo: int
    misses: dict = field(default_factory=dict)   # char -> times missed this run
    failed: bool = False
    difficulty: str = "normal"
    fail_reason: str = ""
    note: str = ""                                # quote source, snippet name
    events: list = field(default_factory=list)    # (elapsed, correct) per press
    presses: dict = field(default_factory=dict)   # char -> times it was due
    pb_before: float = 0.0                        # personal best going in, 0 if none
