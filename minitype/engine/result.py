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
