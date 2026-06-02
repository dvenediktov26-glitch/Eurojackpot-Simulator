"""Scenario definitions for the operator-focused chapter 3 experiments.

These scenarios support two hypotheses:

H2: changing the jackpot cap changes rollover dynamics, overflow behaviour,
    and volatility of upper-tier payouts.
H3: changing the prize-structure skew changes jackpot accumulation speed and
    rollover behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.prize_pool import CLASS_ALLOCATION_SHARES, PRIZE_POOL_SHARE, RESERVE_FUND_SHARE


@dataclass(frozen=True)
class OperatorExperimentConfig:
    """Shared simulation settings used by the operator experiment runner."""

    draws_per_run: int
    repetitions: int
    tickets_sold_per_draw: int
    prize_pool_share: float
    reserve_fund_share: float
    base_seed: int


@dataclass(frozen=True)
class JackpotCapScenario:
    """Scenario for H2: jackpot-cap sensitivity."""

    name: str
    label_cs: str
    description: str
    jackpot_cap: float
    second_tier_cap: float
    class_allocation_shares: dict[str, float]


@dataclass(frozen=True)
class PrizeStructureScenario:
    """Scenario for H3: prize-structure skew sensitivity."""

    name: str
    label_cs: str
    description: str
    jackpot_cap: float
    second_tier_cap: float
    class_allocation_shares: dict[str, float]


OPERATOR_EXPERIMENT_CONFIG = OperatorExperimentConfig(
    draws_per_run=1000,
    repetitions=200,
    tickets_sold_per_draw=25_000_000,
    prize_pool_share=PRIZE_POOL_SHARE,
    reserve_fund_share=RESERVE_FUND_SHARE,
    base_seed=250426,
)


STANDARD_SHARES = dict(CLASS_ALLOCATION_SHARES)

# H3: jackpot-heavy allocation.
AGGRESSIVE_JACKPOT_SHARES = dict(CLASS_ALLOCATION_SHARES)
AGGRESSIVE_JACKPOT_SHARES["Class 1"] += 0.05
AGGRESSIVE_JACKPOT_SHARES["Class 11"] -= 0.02
AGGRESSIVE_JACKPOT_SHARES["Class 12"] -= 0.03

# H3: flatter distribution with less weight in the jackpot.
FLATTER_SHARES = dict(CLASS_ALLOCATION_SHARES)
FLATTER_SHARES["Class 1"] -= 0.05
FLATTER_SHARES["Class 11"] += 0.02
FLATTER_SHARES["Class 12"] += 0.03


JACKPOT_CAP_SCENARIOS: list[JackpotCapScenario] = [
    JackpotCapScenario(
        name="cap_90m",
        label_cs="90 mil. €",
        description="Nižší strop jackpotu 90 mil. €.",
        jackpot_cap=90_000_000.0,
        second_tier_cap=90_000_000.0,
        class_allocation_shares=dict(STANDARD_SHARES),
    ),
    JackpotCapScenario(
        name="cap_120m",
        label_cs="120 mil. €",
        description="Výchozí strop jackpotu 120 mil. €.",
        jackpot_cap=120_000_000.0,
        second_tier_cap=120_000_000.0,
        class_allocation_shares=dict(STANDARD_SHARES),
    ),
    JackpotCapScenario(
        name="cap_150m",
        label_cs="150 mil. €",
        description="Vyšší strop jackpotu 150 mil. €.",
        jackpot_cap=150_000_000.0,
        second_tier_cap=150_000_000.0,
        class_allocation_shares=dict(STANDARD_SHARES),
    ),
]


PRIZE_STRUCTURE_SCENARIOS: list[PrizeStructureScenario] = [
    PrizeStructureScenario(
        name="structure_standard",
        label_cs="Standardní",
        description="Oficiální rozdělení fondu mezi výherní třídy.",
        jackpot_cap=120_000_000.0,
        second_tier_cap=120_000_000.0,
        class_allocation_shares=dict(STANDARD_SHARES),
    ),
    PrizeStructureScenario(
        name="structure_aggressive",
        label_cs="Vyšší skewness",
        description="Vyšší podíl jackpotu na úkor nižších tříd.",
        jackpot_cap=120_000_000.0,
        second_tier_cap=120_000_000.0,
        class_allocation_shares=dict(AGGRESSIVE_JACKPOT_SHARES),
    ),
    PrizeStructureScenario(
        name="structure_flatter",
        label_cs="Nižší skewness",
        description="Plošší rozdělení s menším podílem jackpotu.",
        jackpot_cap=120_000_000.0,
        second_tier_cap=120_000_000.0,
        class_allocation_shares=dict(FLATTER_SHARES),
    ),
]