from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class Ticket:
    main_numbers: FrozenSet[int]
    euro_numbers: FrozenSet[int]


@dataclass(frozen=True)
class Draw:
    main_numbers: FrozenSet[int]
    euro_numbers: FrozenSet[int]


@dataclass(frozen=True)
class EvaluationResult:
    matched_main: int
    matched_euro: int
    prize_class: str | None