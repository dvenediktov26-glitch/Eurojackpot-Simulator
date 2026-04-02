"""Aggregated result object returned by one backend simulation run.

The frontend consumes a JSON version of this dataclass through Pydantic schemas.
Keeping all summary metrics in one place makes it easier to extend the API and
write tests that validate the model.
"""

from dataclasses import dataclass


@dataclass
class SimulationStats:
    """All summary values produced by one simulation batch."""

    draws_simulated: int
    tickets_played: int
    winning_tickets: int
    prize_class_counts: dict[str, int]
    total_spent: float
    total_won: float
    total_co_winners: int
    average_ticket_popularity: float
    tickets_sold_per_draw: int
    actual_total_won_by_class: dict[str, float]
    total_co_winners_by_class: dict[str, int]
    total_class_fund_by_class: dict[str, float]
    total_ticket_sales: float
    total_prize_pool: float
    prize_pool_share: float
    jackpot_hits: int
    max_jackpot_fund_observed: float
    final_jackpot_carryover: float
    total_jackpot_carryover_generated: float
    total_jackpot_available: float
    total_reserve_fund: float
    jackpot_cap: float
    total_jackpot_overflow_to_class2: float
    total_class2_overflow_to_class3: float

    @property
    def net_result(self) -> float:
        """Return the player's profit or loss."""
        return self.total_won - self.total_spent

    @property
    def rtp(self) -> float:
        """Return-to-player ratio for the simulated user."""
        if self.total_spent == 0:
            return 0.0
        return self.total_won / self.total_spent

    @property
    def winning_ticket_ratio(self) -> float:
        """Share of simulated tickets that won any prize class."""
        if self.tickets_played == 0:
            return 0.0
        return self.winning_tickets / self.tickets_played

    @property
    def average_prize_pool_per_draw(self) -> float:
        """Average prize pool size across all simulated draws."""
        if self.draws_simulated == 0:
            return 0.0
        return self.total_prize_pool / self.draws_simulated

    @property
    def average_ticket_sales_per_draw(self) -> float:
        """Average gross revenue from ticket sales per draw."""
        if self.draws_simulated == 0:
            return 0.0
        return self.total_ticket_sales / self.draws_simulated

    @property
    def average_jackpot_carryover_per_draw(self) -> float:
        """Average carryover amount that rolled into the next draw."""
        if self.draws_simulated == 0:
            return 0.0
        return self.total_jackpot_carryover_generated / self.draws_simulated

    @property
    def average_jackpot_available_per_draw(self) -> float:
        """Average jackpot amount available to be won in each draw."""
        if self.draws_simulated == 0:
            return 0.0
        return self.total_jackpot_available / self.draws_simulated

    @property
    def average_reserve_fund_per_draw(self) -> float:
        """Average reserve / booster fund amount per draw."""
        if self.draws_simulated == 0:
            return 0.0
        return self.total_reserve_fund / self.draws_simulated
