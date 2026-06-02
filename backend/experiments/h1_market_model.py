"""Analytical market model for H1: non-random choice and parimutuel dilution.

This version is aligned with the original H1 hypothesis:

Non-random (conscious) number choice by players systematically lowers the
median individual payout due to stronger parimutuel dilution and increases
return variance under a fixed aggregate prize pool.

Unlike the previous H1 version that focused mainly on the top classes,
this implementation evaluates all prize classes and tracks individual
winner-level outcomes in weighted form.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from math import comb
from statistics import mean

from app.core.config import TICKET_PRICE_EUR
from app.core.odds import PRIZE_CLASS_MATCHES
from app.core.prize_pool import CLASS_ALLOCATION_SHARES
from app.core.share_model import sample_poisson

from experiments.h1_choice_scenarios import (
    ALL_TICKET_COUNT,
    DATE_ONLY_MAIN_MAX,
    DATE_ONLY_TICKET_COUNT,
    EURO_PICK_COUNT,
    EURO_POOL_SIZE,
    H1ExperimentConfig,
    MAIN_PICK_COUNT,
    MAIN_POOL_SIZE,
    POPULAR_TICKETS,
    ChoiceScenario,
)

Ticket = tuple[tuple[int, ...], tuple[int, ...]]


def class_number(class_key: str) -> int:
    """Convert class label like 'Class 7' to integer 7."""
    return int(class_key.split()[1])


CLASS_KEYS = sorted(PRIZE_CLASS_MATCHES.keys(), key=class_number)
MATCH_TO_CLASS = {tuple(match_tuple): prize_class for prize_class, match_tuple in PRIZE_CLASS_MATCHES.items()}


@dataclass(frozen=True)
class H1ClassStats:
    """Per-class statistics for one repetition of H1."""

    class_key: str
    class_number: int
    hit_draws: int
    total_winners: int
    mean_winners_per_draw: float
    mean_winners_when_hit: float
    mean_individual_payout: float
    median_individual_payout: float
    payout_variance: float
    mean_individual_return: float
    median_individual_return: float
    return_variance: float


@dataclass(frozen=True)
class H1RunStats:
    """Aggregated statistics for one repetition of H1."""

    draws_simulated: int
    tickets_sold_per_draw: int
    total_ticket_sales: float
    total_theoretical_prize_pool: float
    total_actual_payout: float

    winner_ticket_count: int
    winner_ticket_share: float

    mean_individual_payout_winners: float
    median_individual_payout_winners: float
    payout_variance_winners: float

    mean_individual_return_winners: float
    median_individual_return_winners: float
    return_variance_winners: float

    mean_return_all_tickets: float
    return_variance_all_tickets: float

    exact_ticket_hhi: float
    effective_ticket_support: float
    max_exact_ticket_probability: float

    class_stats: dict[str, H1ClassStats]


def weighted_stats(observations: list[tuple[float, int]]) -> tuple[float, float, float, int]:
    """Return weighted mean, weighted median, weighted variance, total weight.

    observations contains tuples of (value, multiplicity), where multiplicity
    represents how many winners received the same individual payout / return.
    """
    if not observations:
        return 0.0, 0.0, 0.0, 0

    total_weight = sum(weight for _, weight in observations)
    weighted_mean = sum(value * weight for value, weight in observations) / total_weight

    weighted_variance = (
        sum(weight * ((value - weighted_mean) ** 2) for value, weight in observations)
        / total_weight
    )

    sorted_observations = sorted(observations, key=lambda item: item[0])
    threshold = total_weight / 2.0
    cumulative_weight = 0
    weighted_median = 0.0

    for value, weight in sorted_observations:
        cumulative_weight += weight
        if cumulative_weight >= threshold:
            weighted_median = value
            break

    return weighted_mean, weighted_median, weighted_variance, total_weight


def is_date_ticket(ticket: Ticket) -> bool:
    """Return True if all main numbers are within the date-style range 1..31."""
    return max(ticket[0]) <= DATE_ONLY_MAIN_MAX


def draw_uniform_winning_ticket(rng: random.Random) -> Ticket:
    """Draw one winning Eurojackpot combination uniformly."""
    main_numbers = tuple(sorted(rng.sample(range(1, MAIN_POOL_SIZE + 1), MAIN_PICK_COUNT)))
    euro_numbers = tuple(sorted(rng.sample(range(1, EURO_POOL_SIZE + 1), EURO_PICK_COUNT)))
    return main_numbers, euro_numbers


def ticket_match_to_prize_class(ticket: Ticket, winning_ticket: Ticket) -> str | None:
    """Return prize-class key for a ticket, or None if the ticket does not win."""
    main_matches = len(set(ticket[0]) & set(winning_ticket[0]))
    euro_matches = len(set(ticket[1]) & set(winning_ticket[1]))
    return MATCH_TO_CLASS.get((main_matches, euro_matches))


def euro_match_probability(euro_matches: int) -> float:
    """Exact euro-number match probability for one random ticket."""
    return (
        comb(EURO_PICK_COUNT, euro_matches)
        * comb(EURO_POOL_SIZE - EURO_PICK_COUNT, EURO_PICK_COUNT - euro_matches)
        / comb(EURO_POOL_SIZE, EURO_PICK_COUNT)
    )


def uniform_component_class_probability(prize_class: str) -> float:
    """Class probability under fully uniform ticket selection."""
    main_matches, euro_matches = PRIZE_CLASS_MATCHES[prize_class]
    main_probability = (
        comb(MAIN_PICK_COUNT, main_matches)
        * comb(MAIN_POOL_SIZE - MAIN_PICK_COUNT, MAIN_PICK_COUNT - main_matches)
        / comb(MAIN_POOL_SIZE, MAIN_PICK_COUNT)
    )
    return main_probability * euro_match_probability(euro_matches)


def date_component_class_probability(prize_class: str, winning_main_leq_31: int) -> float:
    """Class probability under date-only main-number selection."""
    main_matches, euro_matches = PRIZE_CLASS_MATCHES[prize_class]

    if main_matches > winning_main_leq_31:
        return 0.0

    missing_main_numbers = MAIN_PICK_COUNT - main_matches
    remaining_date_numbers = DATE_ONLY_MAIN_MAX - winning_main_leq_31

    if missing_main_numbers > remaining_date_numbers:
        return 0.0

    main_probability = (
        comb(winning_main_leq_31, main_matches)
        * comb(remaining_date_numbers, missing_main_numbers)
        / comb(DATE_ONLY_MAIN_MAX, MAIN_PICK_COUNT)
    )
    return main_probability * euro_match_probability(euro_matches)


def popular_component_class_probability_map(
    scenario: ChoiceScenario,
    winning_ticket: Ticket,
) -> dict[str, float]:
    """Return class-probability map induced by the exact popular-ticket bank."""
    probability_map: dict[str, float] = {}

    for ticket, weight in zip(POPULAR_TICKETS, scenario.popular_ticket_weights):
        prize_class = ticket_match_to_prize_class(ticket, winning_ticket)
        if prize_class is None:
            continue
        probability_map[prize_class] = probability_map.get(prize_class, 0.0) + weight

    return probability_map


def base_exact_ticket_probability(scenario: ChoiceScenario, ticket: Ticket) -> float:
    """Exact selection probability from non-popular components only."""
    probability = scenario.uniform_share / ALL_TICKET_COUNT
    if is_date_ticket(ticket):
        probability += scenario.date_only_share / DATE_ONLY_TICKET_COUNT
    return probability


def exact_ticket_probability(scenario: ChoiceScenario, ticket: Ticket) -> float:
    """Exact market probability of one specific ticket."""
    probability = base_exact_ticket_probability(scenario, ticket)

    for popular_ticket, weight in zip(POPULAR_TICKETS, scenario.popular_ticket_weights):
        if ticket == popular_ticket:
            probability += scenario.popular_share * weight
            break

    return probability


def compute_exact_ticket_hhi(scenario: ChoiceScenario) -> float:
    """Compute Herfindahl-Hirschman concentration index over exact tickets."""
    base_non_date_probability = scenario.uniform_share / ALL_TICKET_COUNT
    base_date_probability = base_non_date_probability + (scenario.date_only_share / DATE_ONLY_TICKET_COUNT)

    hhi = (
        DATE_ONLY_TICKET_COUNT * (base_date_probability ** 2)
        + (ALL_TICKET_COUNT - DATE_ONLY_TICKET_COUNT) * (base_non_date_probability ** 2)
    )

    for popular_ticket, weight in zip(POPULAR_TICKETS, scenario.popular_ticket_weights):
        base_probability = base_date_probability if is_date_ticket(popular_ticket) else base_non_date_probability
        adjusted_probability = base_probability + scenario.popular_share * weight
        hhi += adjusted_probability ** 2 - base_probability ** 2

    return hhi


def compute_max_exact_ticket_probability(scenario: ChoiceScenario) -> float:
    """Return the maximum probability assigned to any exact ticket."""
    base_non_date_probability = scenario.uniform_share / ALL_TICKET_COUNT
    base_date_probability = base_non_date_probability + (scenario.date_only_share / DATE_ONLY_TICKET_COUNT)

    max_probability = max(base_non_date_probability, base_date_probability)

    for popular_ticket in POPULAR_TICKETS:
        max_probability = max(max_probability, exact_ticket_probability(scenario, popular_ticket))

    return max_probability


def allocate_class_funds(prize_pool: float) -> dict[str, float]:
    """Allocate the prize pool into class funds using the existing project shares."""
    return {
        prize_class: prize_pool * share
        for prize_class, share in CLASS_ALLOCATION_SHARES.items()
    }


def run_h1_market_experiment(
    config: H1ExperimentConfig,
    scenario: ChoiceScenario,
    seed: int,
) -> H1RunStats:
    """Run one repetition of H1."""
    scenario.validate()

    rng = random.Random(seed)
    ticket_sales_per_draw = config.tickets_sold_per_draw * TICKET_PRICE_EUR
    theoretical_prize_pool_per_draw = ticket_sales_per_draw * config.prize_pool_share
    class_funds = allocate_class_funds(theoretical_prize_pool_per_draw)

    class_hit_draws = {class_key: 0 for class_key in CLASS_KEYS}
    class_total_winners = {class_key: 0 for class_key in CLASS_KEYS}

    class_payout_observations: dict[str, list[tuple[float, int]]] = {
        class_key: [] for class_key in CLASS_KEYS
    }
    class_return_observations: dict[str, list[tuple[float, int]]] = {
        class_key: [] for class_key in CLASS_KEYS
    }

    overall_payout_observations: list[tuple[float, int]] = []
    overall_return_observations: list[tuple[float, int]] = []

    total_actual_payout = 0.0
    winner_ticket_count = 0
    total_return_square_sum_all_tickets = 0.0

    for _draw_index in range(config.draws_per_run):
        winning_ticket = draw_uniform_winning_ticket(rng)
        winning_main_leq_31 = sum(1 for number in winning_ticket[0] if number <= DATE_ONLY_MAIN_MAX)

        popular_probability_map = popular_component_class_probability_map(scenario, winning_ticket)

        for class_key in CLASS_KEYS:
            uniform_probability = uniform_component_class_probability(class_key)
            date_probability = date_component_class_probability(class_key, winning_main_leq_31)
            popular_probability = popular_probability_map.get(class_key, 0.0)

            class_probability = (
                scenario.uniform_share * uniform_probability
                + scenario.date_only_share * date_probability
                + scenario.popular_share * popular_probability
            )

            winner_count = sample_poisson(config.tickets_sold_per_draw * class_probability, rng)
            if winner_count <= 0:
                continue

            class_hit_draws[class_key] += 1
            class_total_winners[class_key] += winner_count

            payout_per_winner = class_funds[class_key] / winner_count
            return_per_winner = payout_per_winner / TICKET_PRICE_EUR

            class_payout_observations[class_key].append((payout_per_winner, winner_count))
            class_return_observations[class_key].append((return_per_winner, winner_count))

            overall_payout_observations.append((payout_per_winner, winner_count))
            overall_return_observations.append((return_per_winner, winner_count))

            total_actual_payout += class_funds[class_key]
            winner_ticket_count += winner_count
            total_return_square_sum_all_tickets += winner_count * (return_per_winner ** 2)

    class_stats: dict[str, H1ClassStats] = {}

    for class_key in CLASS_KEYS:
        mean_payout, median_payout, payout_variance, _ = weighted_stats(class_payout_observations[class_key])
        mean_return, median_return, return_variance, _ = weighted_stats(class_return_observations[class_key])

        hit_draws = class_hit_draws[class_key]
        total_winners = class_total_winners[class_key]

        class_stats[class_key] = H1ClassStats(
            class_key=class_key,
            class_number=class_number(class_key),
            hit_draws=hit_draws,
            total_winners=total_winners,
            mean_winners_per_draw=total_winners / config.draws_per_run,
            mean_winners_when_hit=(total_winners / hit_draws) if hit_draws > 0 else 0.0,
            mean_individual_payout=mean_payout,
            median_individual_payout=median_payout,
            payout_variance=payout_variance,
            mean_individual_return=mean_return,
            median_individual_return=median_return,
            return_variance=return_variance,
        )

    (
        mean_individual_payout_winners,
        median_individual_payout_winners,
        payout_variance_winners,
        total_winner_observations,
    ) = weighted_stats(overall_payout_observations)

    (
        mean_individual_return_winners,
        median_individual_return_winners,
        return_variance_winners,
        _,
    ) = weighted_stats(overall_return_observations)

    total_tickets = config.draws_per_run * config.tickets_sold_per_draw
    mean_return_all_tickets = (total_actual_payout / TICKET_PRICE_EUR) / total_tickets
    return_variance_all_tickets = (
        total_return_square_sum_all_tickets / total_tickets
        - (mean_return_all_tickets ** 2)
    )
    return_variance_all_tickets = max(return_variance_all_tickets, 0.0)

    exact_ticket_hhi = compute_exact_ticket_hhi(scenario)
    effective_ticket_support = 1.0 / exact_ticket_hhi if exact_ticket_hhi > 0 else 0.0
    max_exact_ticket_probability = compute_max_exact_ticket_probability(scenario)

    return H1RunStats(
        draws_simulated=config.draws_per_run,
        tickets_sold_per_draw=config.tickets_sold_per_draw,
        total_ticket_sales=ticket_sales_per_draw * config.draws_per_run,
        total_theoretical_prize_pool=theoretical_prize_pool_per_draw * config.draws_per_run,
        total_actual_payout=total_actual_payout,
        winner_ticket_count=winner_ticket_count,
        winner_ticket_share=(winner_ticket_count / total_tickets) if total_tickets > 0 else 0.0,
        mean_individual_payout_winners=mean_individual_payout_winners,
        median_individual_payout_winners=median_individual_payout_winners,
        payout_variance_winners=payout_variance_winners,
        mean_individual_return_winners=mean_individual_return_winners,
        median_individual_return_winners=median_individual_return_winners,
        return_variance_winners=return_variance_winners,
        mean_return_all_tickets=mean_return_all_tickets,
        return_variance_all_tickets=return_variance_all_tickets,
        exact_ticket_hhi=exact_ticket_hhi,
        effective_ticket_support=effective_ticket_support,
        max_exact_ticket_probability=max_exact_ticket_probability,
        class_stats=class_stats,
    )