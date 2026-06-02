"""Operator-side simulation helpers for the redesigned chapter 3 experiments.

The production backend focuses on one fixed user ticket. For the thesis
experiments below we need system-level metrics instead:
- jackpot carryover dynamics,
- upper-tier payout volatility,
- overflow triggered by jackpot caps,
- and the effect of prize-structure changes.

This module keeps that logic separate so the current web API can stay unchanged.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean, pstdev

from app.core.config import TICKET_PRICE_EUR
from app.core.odds import PRIZE_CLASS_MATCHES, get_prize_class_probabilities
from app.core.share_model import sample_poisson

JACKPOT_CLASS_KEY = "Class 1"
SECOND_CLASS_KEY = "Class 2"
THIRD_CLASS_KEY = "Class 3"
UPPER_TIER_KEYS = (JACKPOT_CLASS_KEY, SECOND_CLASS_KEY, THIRD_CLASS_KEY)
PRIZE_CLASS_PROBABILITIES = get_prize_class_probabilities()


@dataclass(frozen=True)
class OperatorDrawMetrics:
    """System-level draw metrics for one simulated draw."""

    draw_index: int
    prize_pool: float
    reserve_fund: float
    jackpot_available_before_draw: float
    effective_jackpot_fund: float
    class2_available_before_draw: float
    effective_class2_fund: float
    effective_class3_fund: float
    jackpot_hit: bool
    jackpot_winners: int
    cap_reached: bool
    overflow_to_class2: float
    overflow_to_class3: float
    actual_total_payout: float
    actual_upper_tier_payout: float
    carryover_after_draw: float


@dataclass(frozen=True)
class OperatorRunStats:
    """Aggregated metrics for one full run of many draws."""

    draws_simulated: int
    tickets_sold_per_draw: int
    prize_pool_share: float
    jackpot_cap: float
    total_ticket_sales: float
    total_prize_pool: float
    total_reserve_fund: float
    total_actual_payout: float
    total_actual_upper_tier_payout: float
    jackpot_hits: int
    jackpot_cap_hits: int
    cap_reach_count: int
    total_overflow_to_class2: float
    total_overflow_to_class3: float
    max_jackpot_fund_observed: float
    final_jackpot_carryover: float
    average_jackpot_available: float
    average_total_payout: float
    payout_std_dev: float
    upper_tier_payout_std_dev: float
    average_rollover_length: float
    longest_rollover_length: int
    average_time_to_cap: float


@dataclass(frozen=True)
class LotteryDesign:
    """Scenario-specific lottery parameters used in operator experiments."""

    prize_pool_share: float
    reserve_fund_share: float
    jackpot_cap: float
    second_tier_cap: float
    class_allocation_shares: dict[str, float]


def validate_lottery_design(design: LotteryDesign) -> None:
    """Validate a scenario before a long Monte Carlo run starts."""
    if not 0 <= design.prize_pool_share <= 1:
        raise ValueError("prize_pool_share must be between 0 and 1.")

    if design.reserve_fund_share < 0:
        raise ValueError("reserve_fund_share must be non-negative.")

    if design.jackpot_cap <= 0 or design.second_tier_cap <= 0:
        raise ValueError("Jackpot caps must be positive.")

    share_total = sum(design.class_allocation_shares.values())
    if abs((share_total + design.reserve_fund_share) - 1.0) > 1e-9:
        raise ValueError(
            "Class allocation shares plus reserve_fund_share must sum to 1.0."
        )

    missing = set(PRIZE_CLASS_MATCHES) - set(design.class_allocation_shares)
    if missing:
        raise ValueError(f"Missing allocation shares for classes: {sorted(missing)}")


def calculate_ticket_sales(tickets_sold_per_draw: int) -> float:
    """Convert tickets sold into gross draw revenue."""
    if tickets_sold_per_draw < 0:
        raise ValueError("tickets_sold_per_draw must be non-negative.")
    return tickets_sold_per_draw * TICKET_PRICE_EUR


def allocate_prize_pool(prize_pool: float, design: LotteryDesign) -> tuple[dict[str, float], float]:
    """Split the draw prize pool into class funds plus reserve fund."""
    class_funds = {
        prize_class: prize_pool * share
        for prize_class, share in design.class_allocation_shares.items()
    }
    reserve_fund = prize_pool * design.reserve_fund_share
    return class_funds, reserve_fund


def sample_winner_counts(tickets_sold_per_draw: int, rng: random.Random) -> dict[str, int]:
    """Sample system-wide winner counts for all prize classes.

    The operator-facing experiment does not track specific tickets. Instead it
    draws a Poisson count for each class using the exact combinatorial class
    probability and the number of sold tickets.
    """
    winner_counts: dict[str, int] = {}

    for prize_class, probability in PRIZE_CLASS_PROBABILITIES.items():
        lam = tickets_sold_per_draw * probability
        winner_counts[prize_class] = sample_poisson(lam, rng)

    return winner_counts


def summarize_rollover_lengths(draw_metrics: list[OperatorDrawMetrics]) -> tuple[float, int]:
    """Return average and maximum rollover streak length."""
    streaks: list[int] = []
    current = 0

    for metric in draw_metrics:
        if metric.jackpot_hit:
            if current > 0:
                streaks.append(current)
            current = 0
        else:
            current += 1

    if current > 0:
        streaks.append(current)

    if not streaks:
        return 0.0, 0

    return mean(streaks), max(streaks)


def summarize_time_to_cap(draw_metrics: list[OperatorDrawMetrics]) -> tuple[float, int]:
    """Return average draws needed to reach the cap and the number of cap cycles.

    A cycle starts after a jackpot hit (or at the start of the simulation) and
    ends when the jackpot is hit. The first draw in the cycle where the cap is
    reached is recorded as that cycle's time-to-cap.
    """
    cycle_draw_index = 0
    cap_reached_in_cycle = False
    times_to_cap: list[int] = []

    for metric in draw_metrics:
        cycle_draw_index += 1

        if metric.cap_reached and not cap_reached_in_cycle:
            times_to_cap.append(cycle_draw_index)
            cap_reached_in_cycle = True

        if metric.jackpot_hit:
            cycle_draw_index = 0
            cap_reached_in_cycle = False

    if not times_to_cap:
        return 0.0, 0

    return mean(times_to_cap), len(times_to_cap)


def run_operator_simulation(
    draws: int,
    tickets_sold_per_draw: int,
    design: LotteryDesign,
    seed: int,
) -> OperatorRunStats:
    """Run one operator-side Monte Carlo simulation."""
    validate_lottery_design(design)

    rng = random.Random(seed)
    jackpot_carryover = 0.0
    draw_metrics: list[OperatorDrawMetrics] = []

    total_ticket_sales = 0.0
    total_prize_pool = 0.0
    total_reserve_fund = 0.0
    total_actual_payout = 0.0
    total_actual_upper_tier_payout = 0.0
    jackpot_hits = 0
    jackpot_cap_hits = 0
    total_overflow_to_class2 = 0.0
    total_overflow_to_class3 = 0.0
    max_jackpot_fund_observed = 0.0

    for draw_index in range(1, draws + 1):
        ticket_sales = calculate_ticket_sales(tickets_sold_per_draw)
        prize_pool = ticket_sales * design.prize_pool_share
        class_funds, reserve_fund = allocate_prize_pool(prize_pool, design)
        winner_counts = sample_winner_counts(tickets_sold_per_draw, rng)

        total_ticket_sales += ticket_sales
        total_prize_pool += prize_pool
        total_reserve_fund += reserve_fund

        jackpot_available = class_funds[JACKPOT_CLASS_KEY] + jackpot_carryover
        overflow_to_class2 = max(0.0, jackpot_available - design.jackpot_cap)
        effective_jackpot_fund = min(jackpot_available, design.jackpot_cap)
        cap_reached = jackpot_available >= design.jackpot_cap

        class2_available = class_funds[SECOND_CLASS_KEY] + overflow_to_class2
        overflow_to_class3 = max(0.0, class2_available - design.second_tier_cap)
        effective_class2_fund = min(class2_available, design.second_tier_cap)
        effective_class3_fund = class_funds[THIRD_CLASS_KEY] + overflow_to_class3

        effective_class_funds = dict(class_funds)
        effective_class_funds[JACKPOT_CLASS_KEY] = effective_jackpot_fund
        effective_class_funds[SECOND_CLASS_KEY] = effective_class2_fund
        effective_class_funds[THIRD_CLASS_KEY] = effective_class3_fund

        actual_total_payout = 0.0
        actual_upper_tier_payout = 0.0

        for prize_class, class_fund in effective_class_funds.items():
            if winner_counts[prize_class] > 0:
                actual_total_payout += class_fund
                if prize_class in UPPER_TIER_KEYS:
                    actual_upper_tier_payout += class_fund

        jackpot_hit = winner_counts[JACKPOT_CLASS_KEY] > 0
        if jackpot_hit:
            jackpot_hits += 1
            jackpot_carryover = 0.0
        else:
            jackpot_carryover = effective_jackpot_fund

        if cap_reached:
            jackpot_cap_hits += 1

        total_actual_payout += actual_total_payout
        total_actual_upper_tier_payout += actual_upper_tier_payout
        total_overflow_to_class2 += overflow_to_class2
        total_overflow_to_class3 += overflow_to_class3
        max_jackpot_fund_observed = max(max_jackpot_fund_observed, effective_jackpot_fund)

        draw_metrics.append(
            OperatorDrawMetrics(
                draw_index=draw_index,
                prize_pool=prize_pool,
                reserve_fund=reserve_fund,
                jackpot_available_before_draw=jackpot_available,
                effective_jackpot_fund=effective_jackpot_fund,
                class2_available_before_draw=class2_available,
                effective_class2_fund=effective_class2_fund,
                effective_class3_fund=effective_class3_fund,
                jackpot_hit=jackpot_hit,
                jackpot_winners=winner_counts[JACKPOT_CLASS_KEY],
                cap_reached=cap_reached,
                overflow_to_class2=overflow_to_class2,
                overflow_to_class3=overflow_to_class3,
                actual_total_payout=actual_total_payout,
                actual_upper_tier_payout=actual_upper_tier_payout,
                carryover_after_draw=jackpot_carryover,
            )
        )

    average_rollover_length, longest_rollover_length = summarize_rollover_lengths(draw_metrics)
    average_time_to_cap, cap_reach_count = summarize_time_to_cap(draw_metrics)

    jackpot_available_values = [m.jackpot_available_before_draw for m in draw_metrics]
    total_payout_values = [m.actual_total_payout for m in draw_metrics]
    upper_tier_payout_values = [m.actual_upper_tier_payout for m in draw_metrics]

    return OperatorRunStats(
        draws_simulated=draws,
        tickets_sold_per_draw=tickets_sold_per_draw,
        prize_pool_share=design.prize_pool_share,
        jackpot_cap=design.jackpot_cap,
        total_ticket_sales=total_ticket_sales,
        total_prize_pool=total_prize_pool,
        total_reserve_fund=total_reserve_fund,
        total_actual_payout=total_actual_payout,
        total_actual_upper_tier_payout=total_actual_upper_tier_payout,
        jackpot_hits=jackpot_hits,
        jackpot_cap_hits=jackpot_cap_hits,
        cap_reach_count=cap_reach_count,
        total_overflow_to_class2=total_overflow_to_class2,
        total_overflow_to_class3=total_overflow_to_class3,
        max_jackpot_fund_observed=max_jackpot_fund_observed,
        final_jackpot_carryover=jackpot_carryover,
        average_jackpot_available=mean(jackpot_available_values),
        average_total_payout=mean(total_payout_values),
        payout_std_dev=pstdev(total_payout_values),
        upper_tier_payout_std_dev=pstdev(upper_tier_payout_values),
        average_rollover_length=average_rollover_length,
        longest_rollover_length=longest_rollover_length,
        average_time_to_cap=average_time_to_cap,
    )