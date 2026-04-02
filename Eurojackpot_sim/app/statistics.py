"""Legacy statistics container from the original command-line version."""

from collections import Counter
from dataclasses import dataclass


@dataclass
class SimulationStats:
    draws_simulated: int
    tickets_played: int
    winning_tickets: int
    prize_class_counts: dict[str, int]
    total_spent: float
    total_won: float

    @property
    def net_result(self) -> float:
        return self.total_won - self.total_spent

    @property
    def rtp(self) -> float:
        if self.total_spent == 0:
            return 0.0
        return self.total_won / self.total_spent

    @property
    def winning_ticket_ratio(self) -> float:
        if self.tickets_played == 0:
            return 0.0
        return self.winning_tickets / self.tickets_played


def empty_prize_counter() -> Counter:
    return Counter()