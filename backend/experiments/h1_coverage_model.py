"""Analytical and simulation helpers for H1: coverage gap and rollover acceleration."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from app.core.prize_pool import CLASS_ALLOCATION_SHARES, calculate_prize_pool
from experiments.h1_coverage_scenarios import (
    DATE_ONLY_JACKPOT_COMBINATIONS,
    H1CoverageConfig,
    TOTAL_JACKPOT_COMBINATIONS,
    CoverageScenario,
)

JACKPOT_CLASS_KEY = "Class 1"


@dataclass(frozen=True)
class CoverageMetrics:
    """Deterministic market-coverage metrics implied by one scenario."""

    expected_unique_coverage: float
    coverage_ratio: float
    jackpot_hit_probability: float
    no_jackpot_winner_probability: float
    expected_draws_until_jackpot_hit: float
    exact_ticket_hhi: float
    effective_ticket_support: float
    max_exact_ticket_probability: float


@dataclass(frozen=True)
class CoverageRunStats:
    """Simulation output for one repetition of the coverage-gap experiment."""

    jackpot_hit_probability: float
    no_jackpot_winner_probability: float
    expected_unique_coverage: float
    coverage_ratio: float
    exact_ticket_hhi: float
    effective_ticket_support: float
    max_exact_ticket_probability: float
    mean_draws_until_jackpot_hit: float
    mean_misses_before_jackpot_hit: float
    jackpot_hit_count: int
    no_winner_draw_share: float
    mean_time_to_cap: float | None
    reached_cap: bool
    max_jackpot_fund_observed: float
    average_jackpot_available: float
    total_overflow_to_class2: float
    draws_at_cap: int


def probability_any_purchase(ticket_probability: float, tickets_sold: int) -> float:
    """Return probability that at least one of N sold tickets equals one exact ticket."""
    if ticket_probability <= 0.0:
        return 0.0

    exponent = tickets_sold * math.log1p(-ticket_probability)
    return -math.expm1(exponent)


def scenario_group_probabilities(scenario: CoverageScenario) -> tuple[float, float, list[float]]:
    """Return exact-ticket probabilities for the three ticket groups.

    Returns:
        non_date_probability,
        date_nonpopular_probability,
        popular_ticket_probabilities
    """
    scenario.validate()

    total = TOTAL_JACKPOT_COMBINATIONS
    date_space = DATE_ONLY_JACKPOT_COMBINATIONS

    uniform_part = scenario.uniform_share / total
    date_part = scenario.date_only_share / date_space

    non_date_probability = uniform_part
    date_nonpopular_probability = uniform_part + date_part
    popular_probabilities = [
        date_nonpopular_probability + scenario.popular_share * weight
        for weight in scenario.popular_exact_ticket_weights
    ]

    return non_date_probability, date_nonpopular_probability, popular_probabilities


def compute_coverage_metrics(
    scenario: CoverageScenario,
    tickets_sold_per_draw: int,
) -> CoverageMetrics:
    """Compute analytical market-coverage metrics for one scenario."""
    total = TOTAL_JACKPOT_COMBINATIONS
    date_space = DATE_ONLY_JACKPOT_COMBINATIONS
    popular_count = len(scenario.popular_exact_ticket_weights)

    non_date_count = total - date_space
    date_nonpopular_count = date_space - popular_count

    p_non_date, p_date_nonpopular, p_popular = scenario_group_probabilities(scenario)

    expected_unique_non_date = non_date_count * probability_any_purchase(p_non_date, tickets_sold_per_draw)
    expected_unique_date_nonpopular = date_nonpopular_count * probability_any_purchase(
        p_date_nonpopular,
        tickets_sold_per_draw,
    )
    expected_unique_popular = sum(
        probability_any_purchase(probability, tickets_sold_per_draw)
        for probability in p_popular
    )

    expected_unique_coverage = (
        expected_unique_non_date
        + expected_unique_date_nonpopular
        + expected_unique_popular
    )
    coverage_ratio = expected_unique_coverage / total
    jackpot_hit_probability = coverage_ratio
    no_jackpot_winner_probability = 1.0 - jackpot_hit_probability
    expected_draws_until_jackpot_hit = 1.0 / jackpot_hit_probability

    exact_ticket_hhi = (
        non_date_count * (p_non_date**2)
        + date_nonpopular_count * (p_date_nonpopular**2)
        + sum(probability**2 for probability in p_popular)
    )
    effective_ticket_support = 1.0 / exact_ticket_hhi
    max_exact_ticket_probability = max([p_non_date, p_date_nonpopular, *p_popular])

    return CoverageMetrics(
        expected_unique_coverage=expected_unique_coverage,
        coverage_ratio=coverage_ratio,
        jackpot_hit_probability=jackpot_hit_probability,
        no_jackpot_winner_probability=no_jackpot_winner_probability,
        expected_draws_until_jackpot_hit=expected_draws_until_jackpot_hit,
        exact_ticket_hhi=exact_ticket_hhi,
        effective_ticket_support=effective_ticket_support,
        max_exact_ticket_probability=max_exact_ticket_probability,
    )


def run_h1_coverage_simulation(
    config: H1CoverageConfig,
    scenario: CoverageScenario,
    seed: int,
) -> CoverageRunStats:
    """Simulate jackpot-only system dynamics implied by one market profile."""
    rng = random.Random(seed)
    metrics = compute_coverage_metrics(scenario, config.tickets_sold_per_draw)

    prize_pool = calculate_prize_pool(config.tickets_sold_per_draw)
    jackpot_base_fund = prize_pool * CLASS_ALLOCATION_SHARES[JACKPOT_CLASS_KEY]

    jackpot_carryover = 0.0
    jackpot_waits: list[int] = []
    misses_before_hit: list[int] = []
    current_miss_streak = 0

    no_winner_draws = 0
    time_to_cap: int | None = None
    draws_at_cap = 0
    max_jackpot_fund_observed = 0.0
    total_jackpot_available = 0.0
    total_overflow_to_class2 = 0.0
    jackpot_hit_count = 0

    for draw_index in range(config.draws_per_run):
        jackpot_available = jackpot_base_fund + jackpot_carryover
        overflow_to_class2 = max(0.0, jackpot_available - config.jackpot_cap_eur)
        effective_jackpot_fund = min(jackpot_available, config.jackpot_cap_eur)

        total_jackpot_available += effective_jackpot_fund
        total_overflow_to_class2 += overflow_to_class2
        max_jackpot_fund_observed = max(max_jackpot_fund_observed, effective_jackpot_fund)

        if effective_jackpot_fund >= config.jackpot_cap_eur:
            draws_at_cap += 1
            if time_to_cap is None:
                time_to_cap = draw_index + 1

        jackpot_hit = rng.random() < metrics.jackpot_hit_probability

        if jackpot_hit:
            jackpot_hit_count += 1
            jackpot_waits.append(current_miss_streak + 1)
            misses_before_hit.append(current_miss_streak)
            current_miss_streak = 0
            jackpot_carryover = 0.0
        else:
            no_winner_draws += 1
            current_miss_streak += 1
            jackpot_carryover = effective_jackpot_fund

    mean_draws_until_jackpot_hit = (
        sum(jackpot_waits) / len(jackpot_waits) if jackpot_waits else float("inf")
    )
    mean_misses_before_jackpot_hit = (
        sum(misses_before_hit) / len(misses_before_hit) if misses_before_hit else float("inf")
    )

    return CoverageRunStats(
        jackpot_hit_probability=metrics.jackpot_hit_probability,
        no_jackpot_winner_probability=metrics.no_jackpot_winner_probability,
        expected_unique_coverage=metrics.expected_unique_coverage,
        coverage_ratio=metrics.coverage_ratio,
        exact_ticket_hhi=metrics.exact_ticket_hhi,
        effective_ticket_support=metrics.effective_ticket_support,
        max_exact_ticket_probability=metrics.max_exact_ticket_probability,
        mean_draws_until_jackpot_hit=mean_draws_until_jackpot_hit,
        mean_misses_before_jackpot_hit=mean_misses_before_jackpot_hit,
        jackpot_hit_count=jackpot_hit_count,
        no_winner_draw_share=no_winner_draws / config.draws_per_run,
        mean_time_to_cap=float(time_to_cap) if time_to_cap is not None else None,
        reached_cap=time_to_cap is not None,
        max_jackpot_fund_observed=max_jackpot_fund_observed,
        average_jackpot_available=total_jackpot_available / config.draws_per_run,
        total_overflow_to_class2=total_overflow_to_class2,
        draws_at_cap=draws_at_cap,
    )