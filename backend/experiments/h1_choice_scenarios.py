"""Scenario definitions for H1: non-random player number choice.

This experiment studies how conscious / biased ticket selection affects
parimutuel dilution in the upper prize classes.

The implementation is intentionally self-contained and operator-oriented:
it does not modify the existing backend API and can be run independently
from the previous player-side experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb

from app.core.prize_pool import PRIZE_POOL_SHARE

MAIN_POOL_SIZE = 50
MAIN_PICK_COUNT = 5
EURO_POOL_SIZE = 12
EURO_PICK_COUNT = 2
DATE_ONLY_MAIN_MAX = 31

ALL_TICKET_COUNT = comb(MAIN_POOL_SIZE, MAIN_PICK_COUNT) * comb(EURO_POOL_SIZE, EURO_PICK_COUNT)
DATE_ONLY_TICKET_COUNT = comb(DATE_ONLY_MAIN_MAX, MAIN_PICK_COUNT) * comb(EURO_POOL_SIZE, EURO_PICK_COUNT)

Ticket = tuple[tuple[int, ...], tuple[int, ...]]

# A small bank of "popular" exact tickets. The goal is not to claim that these
# are the only popular combinations in reality, but to create a stable and
# interpretable concentration effect inside the simulation.
POPULAR_TICKETS: tuple[Ticket, ...] = (
    ((1, 2, 3, 4, 5), (1, 2)),
    ((7, 14, 21, 28, 31), (1, 7)),
    ((5, 10, 15, 20, 25), (2, 8)),
    ((3, 13, 23, 30, 31), (3, 9)),
    ((1, 11, 21, 29, 30), (4, 10)),
    ((6, 12, 18, 24, 30), (5, 11)),
    ((8, 16, 24, 28, 31), (6, 12)),
    ((9, 19, 20, 29, 31), (1, 6)),
    ((4, 8, 15, 16, 23), (4, 8)),
    ((10, 20, 21, 22, 23), (2, 12)),
)

POPULAR_TICKET_WEIGHTS: tuple[float, ...] = (
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
class H1ExperimentConfig:
    """Shared simulation settings for H1."""

    draws_per_run: int
    repetitions: int
    tickets_sold_per_draw: int
    prize_pool_share: float
    base_seed: int


@dataclass(frozen=True)
class ChoiceScenario:
    """Scenario for player ticket-selection behaviour."""

    name: str
    label_cs: str
    description: str
    uniform_share: float
    date_only_share: float
    popular_share: float
    popular_ticket_weights: tuple[float, ...]

    def validate(self) -> None:
        component_sum = self.uniform_share + self.date_only_share + self.popular_share
        if abs(component_sum - 1.0) > 1e-12:
            raise ValueError(
                f"Scenario '{self.name}' has component shares summing to {component_sum}, expected 1.0."
            )

        if len(self.popular_ticket_weights) != len(POPULAR_TICKETS):
            raise ValueError(
                f"Scenario '{self.name}' has mismatched popular_ticket_weights length."
            )

        if self.popular_share == 0:
            return

        weight_sum = sum(self.popular_ticket_weights)
        if abs(weight_sum - 1.0) > 1e-12:
            raise ValueError(
                f"Scenario '{self.name}' has popular_ticket_weights summing to {weight_sum}, expected 1.0."
            )


H1_EXPERIMENT_CONFIG = H1ExperimentConfig(
    draws_per_run=1000,
    repetitions=1000,
    tickets_sold_per_draw=10_000_000,
    prize_pool_share=PRIZE_POOL_SHARE,
    base_seed=260426,
)

H1_CHOICE_SCENARIOS: list[ChoiceScenario] = [
    ChoiceScenario(
        name="uniform_market",
        label_cs="Uniformní trh",
        description="Hráči volí kombinace rovnoměrně bez systematického zkreslení.",
        uniform_share=1.0,
        date_only_share=0.0,
        popular_share=0.0,
        popular_ticket_weights=POPULAR_TICKET_WEIGHTS,
    ),
    ChoiceScenario(
        name="mild_bias_market",
        label_cs="Mírně vychýlený trh",
        description=(
            "Část trhu preferuje kalendářní čísla a malá část se koncentruje "
            "na několik populárních tiketů."
        ),
        uniform_share=0.95,
        date_only_share=0.045,
        popular_share=0.005,
        popular_ticket_weights=POPULAR_TICKET_WEIGHTS,
    ),
    ChoiceScenario(
        name="strong_bias_market",
        label_cs="Silně vychýlený trh",
        description=(
            "Výraznější preference kalendářních kombinací a zřetelnější "
            "koncentrace na malé množství populárních tiketů."
        ),
        uniform_share=0.90,
        date_only_share=0.08,
        popular_share=0.02,
        popular_ticket_weights=POPULAR_TICKET_WEIGHTS,
    ),
]