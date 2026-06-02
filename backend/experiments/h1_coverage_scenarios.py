"""Scenario definitions for H1: coverage gap and rollover acceleration.

This experiment studies whether behaviorally clustered ticket selection reduces
combinatorial coverage of the Eurojackpot jackpot space and thereby lowers the
probability that the jackpot is hit in a given draw.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb

from app.core.prize_pool import JACKPOT_CAP

MAIN_POOL_SIZE = 50
MAIN_PICK_COUNT = 5
EURO_POOL_SIZE = 12
EURO_PICK_COUNT = 2
DATE_ONLY_MAIN_MAX = 31

TOTAL_JACKPOT_COMBINATIONS = comb(MAIN_POOL_SIZE, MAIN_PICK_COUNT) * comb(EURO_POOL_SIZE, EURO_PICK_COUNT)
DATE_ONLY_JACKPOT_COMBINATIONS = comb(DATE_ONLY_MAIN_MAX, MAIN_PICK_COUNT) * comb(EURO_POOL_SIZE, EURO_PICK_COUNT)

# The experiment models exact popular tickets, because coverage in jackpot space
# is driven by repeated purchases of the same full 5+2 combination.
POPULAR_EXACT_TICKET_LABELS: tuple[str, ...] = (
    "1-2-3-4-5 + 1-2",
    "7-14-21-28-31 + 1-7",
    "5-10-15-20-25 + 2-8",
    "3-13-23-30-31 + 3-9",
    "1-11-21-29-30 + 4-10",
    "6-12-18-24-30 + 5-11",
    "8-16-24-28-31 + 6-12",
    "9-19-20-29-31 + 1-6",
    "4-8-15-16-23 + 4-8",
    "10-20-21-22-23 + 2-12",
)

POPULAR_EXACT_TICKET_WEIGHTS: tuple[float, ...] = (
    0.18,
    0.14,
    0.12,
    0.10,
    0.10,
    0.09,
    0.08,
    0.07,
    0.07,
    0.05,
)


@dataclass(frozen=True)
class H1CoverageConfig:
    """Shared configuration for the coverage-gap experiment."""

    draws_per_run: int
    repetitions: int
    tickets_sold_per_draw: int
    jackpot_cap_eur: float
    base_seed: int


@dataclass(frozen=True)
class CoverageScenario:
    """One market profile used in the coverage-gap experiment."""

    name: str
    label_cs: str
    description: str
    uniform_share: float
    date_only_share: float
    popular_share: float
    popular_exact_ticket_weights: tuple[float, ...]

    def validate(self) -> None:
        component_sum = self.uniform_share + self.date_only_share + self.popular_share
        if abs(component_sum - 1.0) > 1e-12:
            raise ValueError(
                f"Scenario '{self.name}' has component shares summing to {component_sum}, expected 1.0."
            )

        if len(self.popular_exact_ticket_weights) != len(POPULAR_EXACT_TICKET_WEIGHTS):
            raise ValueError(
                f"Scenario '{self.name}' has an invalid number of popular-ticket weights."
            )

        if self.popular_share == 0.0:
            return

        weight_sum = sum(self.popular_exact_ticket_weights)
        if abs(weight_sum - 1.0) > 1e-12:
            raise ValueError(
                f"Scenario '{self.name}' has popular-ticket weights summing to {weight_sum}, expected 1.0."
            )


H1_COVERAGE_CONFIG = H1CoverageConfig(
    draws_per_run=1000,
    repetitions=1000,
    tickets_sold_per_draw=25_000_000,
    jackpot_cap_eur=JACKPOT_CAP,
    base_seed=260526,
)


H1_COVERAGE_SCENARIOS: list[CoverageScenario] = [
    CoverageScenario(
        name="uniform_market",
        label_cs="Uniformní trh",
        description="100 % trhu vybírá kombinace rovnoměrně v celém jackpotovém prostoru.",
        uniform_share=1.0,
        date_only_share=0.0,
        popular_share=0.0,
        popular_exact_ticket_weights=POPULAR_EXACT_TICKET_WEIGHTS,
    ),
    CoverageScenario(
        name="mildly_clustered_market",
        label_cs="Mírně vychýlený trh",
        description=(
            "80 % trhu vybírá kombinace rovnoměrně, 15 % trhu se soustředí na date-like "
            "kombinace s hlavními čísly 1–31 a 5 % trhu na bank populárních přesných tiketů."
        ),
        uniform_share=0.80,
        date_only_share=0.15,
        popular_share=0.05,
        popular_exact_ticket_weights=POPULAR_EXACT_TICKET_WEIGHTS,
    ),
    CoverageScenario(
        name="strongly_clustered_market",
        label_cs="Silně vychýlený trh",
        description=(
            "60 % trhu vybírá kombinace rovnoměrně, 25 % trhu se soustředí na date-like "
            "kombinace s hlavními čísly 1–31 a 15 % trhu na bank populárních přesných tiketů."
        ),
        uniform_share=0.60,
        date_only_share=0.25,
        popular_share=0.15,
        popular_exact_ticket_weights=POPULAR_EXACT_TICKET_WEIGHTS,
    ),
]