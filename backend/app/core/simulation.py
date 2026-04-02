"""Top-level simulation loop for the production backend.

This module ties all modelling pieces together:
- the official draw generation,
- prize-pool construction,
- jackpot rollover and caps,
- shared winnings,
- and final statistics aggregation.
"""

import random
from collections import Counter
from typing import Literal

from app.core.config import TICKET_PRICE_EUR
from app.core.evaluator import evaluate_ticket
from app.core.generator import generate_draw
from app.core.models import Ticket
from app.core.prize_pool import (
    JACKPOT_CAP,
    PRIZE_POOL_SHARE,
    SECOND_TIER_CAP,
    allocate_prize_pool_by_class,
    calculate_prize_pool,
    calculate_ticket_sales,
)
from app.core.share_model import DEFAULT_TICKETS_SOLD, calculate_shared_payout
from app.core.statistics import SimulationStats

MarketModel = Literal["uniform", "realistic"]
JACKPOT_CLASS_KEY = "Class 1"
SECOND_CLASS_KEY = "Class 2"
THIRD_CLASS_KEY = "Class 3"


def run_simulation(
    n_draws: int,
    user_ticket: Ticket,
    seed: int | None = None,
    market_model: MarketModel = "uniform",
    tickets_sold_per_draw: int = DEFAULT_TICKETS_SOLD,
) -> SimulationStats:
    """Simulate a batch of Eurojackpot draws for one fixed user ticket.

    The frontend uses this function in a batched way: every API request buys a
    number of tickets with the same user-selected numbers and accumulates the
    returned totals on the client side.
    """
    rng = random.Random(seed)

    # Per-class aggregations are stored separately so the frontend can build the
    # prize distribution table and chart.
    prize_class_counts: Counter[str] = Counter()
    actual_total_won_by_class: Counter[str] = Counter()
    total_co_winners_by_class: Counter[str] = Counter()
    total_class_fund_by_class: Counter[str] = Counter()

    winning_tickets = 0
    total_won = 0.0
    total_co_winners = 0
    popularity_score_sum = 0.0
    total_ticket_sales = 0.0
    total_prize_pool = 0.0

    # Jackpot state is carried from one draw into the next.
    jackpot_carryover = 0.0
    jackpot_hits = 0
    max_jackpot_fund_observed = 0.0
    total_jackpot_carryover_generated = 0.0
    total_jackpot_available = 0.0
    total_reserve_fund = 0.0
    total_jackpot_overflow_to_class2 = 0.0
    total_class2_overflow_to_class3 = 0.0

    for _ in range(n_draws):
        ticket_sales = calculate_ticket_sales(tickets_sold_per_draw)
        prize_pool = calculate_prize_pool(tickets_sold_per_draw, PRIZE_POOL_SHARE)
        base_class_funds, reserve_fund = allocate_prize_pool_by_class(prize_pool)

        total_ticket_sales += ticket_sales
        total_prize_pool += prize_pool
        total_reserve_fund += reserve_fund

        # Start with the nominal jackpot share for this draw and add any unpaid
        # jackpot money rolled over from previous draws.
        jackpot_available = base_class_funds[JACKPOT_CLASS_KEY] + jackpot_carryover

        # If the jackpot exceeds the cap, the overflow is redirected to Class 2.
        overflow_to_class2 = max(0.0, jackpot_available - JACKPOT_CAP)
        effective_jackpot_fund = min(jackpot_available, JACKPOT_CAP)

        class2_available = base_class_funds[SECOND_CLASS_KEY] + overflow_to_class2

        # The same logic is applied one tier lower: if Class 2 also exceeds the
        # cap, the remaining amount is redirected to Class 3.
        overflow_to_class3 = max(0.0, class2_available - SECOND_TIER_CAP)
        effective_class2_fund = min(class2_available, SECOND_TIER_CAP)
        effective_class3_fund = base_class_funds[THIRD_CLASS_KEY] + overflow_to_class3

        total_jackpot_available += effective_jackpot_fund
        total_jackpot_overflow_to_class2 += overflow_to_class2
        total_class2_overflow_to_class3 += overflow_to_class3
        max_jackpot_fund_observed = max(max_jackpot_fund_observed, effective_jackpot_fund)

        # The effective class funds are the actual amounts that can be won in
        # this draw after rollover and cap logic has been applied.
        effective_class_funds = dict(base_class_funds)
        effective_class_funds[JACKPOT_CLASS_KEY] = effective_jackpot_fund
        effective_class_funds[SECOND_CLASS_KEY] = effective_class2_fund
        effective_class_funds[THIRD_CLASS_KEY] = effective_class3_fund

        for prize_class, class_fund in effective_class_funds.items():
            total_class_fund_by_class[prize_class] += class_fund

        draw = generate_draw(rng)
        result = evaluate_ticket(user_ticket, draw)

        jackpot_won_this_draw = result.prize_class == JACKPOT_CLASS_KEY

        if result.prize_class is not None:
            winning_tickets += 1
            prize_class_counts[result.prize_class] += 1

            class_fund = effective_class_funds[result.prize_class]
            payout, other_winners, popularity_score = calculate_shared_payout(
                prize_class=result.prize_class,
                ticket=user_ticket,
                class_fund=class_fund,
                tickets_sold=tickets_sold_per_draw,
                market_model=market_model,
                rng=rng,
            )

            total_won += payout
            total_co_winners += other_winners
            popularity_score_sum += popularity_score

            actual_total_won_by_class[result.prize_class] += payout
            total_co_winners_by_class[result.prize_class] += other_winners

            if result.prize_class == JACKPOT_CLASS_KEY:
                jackpot_hits += 1

        # If the jackpot was not won, the capped jackpot amount becomes the next
        # draw's carryover; otherwise the rollover resets to zero.
        if jackpot_won_this_draw:
            jackpot_carryover = 0.0
        else:
            jackpot_carryover = effective_jackpot_fund
            total_jackpot_carryover_generated += jackpot_carryover

    average_ticket_popularity = (
        popularity_score_sum / winning_tickets if winning_tickets > 0 else 0.0
    )

    return SimulationStats(
        draws_simulated=n_draws,
        tickets_played=n_draws,
        winning_tickets=winning_tickets,
        prize_class_counts=dict(prize_class_counts),
        total_spent=n_draws * TICKET_PRICE_EUR,
        total_won=total_won,
        total_co_winners=total_co_winners,
        average_ticket_popularity=average_ticket_popularity,
        tickets_sold_per_draw=tickets_sold_per_draw,
        actual_total_won_by_class=dict(actual_total_won_by_class),
        total_co_winners_by_class=dict(total_co_winners_by_class),
        total_class_fund_by_class=dict(total_class_fund_by_class),
        total_ticket_sales=total_ticket_sales,
        total_prize_pool=total_prize_pool,
        prize_pool_share=PRIZE_POOL_SHARE,
        jackpot_hits=jackpot_hits,
        max_jackpot_fund_observed=max_jackpot_fund_observed,
        final_jackpot_carryover=jackpot_carryover,
        total_jackpot_carryover_generated=total_jackpot_carryover_generated,
        total_jackpot_available=total_jackpot_available,
        total_reserve_fund=total_reserve_fund,
        jackpot_cap=JACKPOT_CAP,
        total_jackpot_overflow_to_class2=total_jackpot_overflow_to_class2,
        total_class2_overflow_to_class3=total_class2_overflow_to_class3,
    )
