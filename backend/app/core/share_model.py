"""Shared-prize model for estimating how many co-winners exist.

When the user wins a prize class, they usually do not receive the full class
fund. The fund is shared between all winning tickets in that class. This module
estimates the number of other winners using exact class odds and a simplified
market-behaviour multiplier.
"""

from __future__ import annotations

import math
import random
from typing import Literal

from app.core.models import Ticket
from app.core.odds import get_prize_class_probabilities
from app.core.popularity import compute_ticket_popularity_score

DEFAULT_TICKETS_SOLD = 10_000_000

# The market mode controls whether other players are assumed to choose tickets
# uniformly or according to the realistic popularity model.
MarketModel = Literal["uniform", "realistic"]
POPULARITY_EXPONENT = 1.0

# Precompute the exact probability of each prize class once at import time.
PRIZE_CLASS_PROBABILITIES = get_prize_class_probabilities()


def sample_poisson(lam: float, rng: random.Random) -> int:
    """Sample from a Poisson distribution.

    For small lambda the exact Knuth algorithm is accurate and simple. For large
    lambda a normal approximation is much faster and sufficiently accurate for
    the simulation's purpose.
    """
    if lam < 0:
        raise ValueError("Lambda must be non-negative.")

    if lam == 0:
        return 0

    if lam < 30:
        limit = math.exp(-lam)
        product = 1.0
        k = 0

        while product > limit:
            k += 1
            product *= rng.random()

        return k - 1

    sampled = rng.gauss(lam, math.sqrt(lam))
    return max(0, int(round(sampled)))


def get_market_popularity_multiplier(
    ticket: Ticket,
    market_model: MarketModel,
) -> float:
    """Return the crowd-size adjustment implied by the market model."""
    if market_model == "uniform":
        return 1.0

    if market_model == "realistic":
        popularity_score = compute_ticket_popularity_score(ticket.main_numbers)
        return popularity_score ** POPULARITY_EXPONENT

    raise ValueError(f"Unsupported market model: {market_model}")


def estimate_lambda_for_ticket(
    prize_class: str,
    ticket: Ticket,
    tickets_sold: int,
    market_model: MarketModel,
) -> float:
    """Estimate the expected number of *other* winners for one class.

    The expected value is: number_of_other_tickets × class_probability ×
    popularity_multiplier.
    """
    if prize_class not in PRIZE_CLASS_PROBABILITIES:
        raise ValueError(f"Unknown prize class: {prize_class}")

    if tickets_sold < 1:
        raise ValueError("tickets_sold must be at least 1.")

    class_probability = PRIZE_CLASS_PROBABILITIES[prize_class]
    popularity_multiplier = get_market_popularity_multiplier(
        ticket=ticket,
        market_model=market_model,
    )

    other_tickets = tickets_sold - 1
    return other_tickets * class_probability * popularity_multiplier


def estimate_other_winners(
    prize_class: str,
    ticket: Ticket,
    tickets_sold: int,
    market_model: MarketModel,
    rng: random.Random,
) -> int:
    """Draw a stochastic number of other winners for one prize class."""
    lam = estimate_lambda_for_ticket(
        prize_class=prize_class,
        ticket=ticket,
        tickets_sold=tickets_sold,
        market_model=market_model,
    )
    return sample_poisson(lam, rng)


def calculate_shared_payout(
    prize_class: str,
    ticket: Ticket,
    class_fund: float,
    tickets_sold: int,
    market_model: MarketModel,
    rng: random.Random,
) -> tuple[float, int, float]:
    """Split a class fund between the user's ticket and estimated co-winners.

    Returns the user's payout, the number of other winners, and the ticket's
    popularity score for later reporting.
    """
    if class_fund < 0:
        raise ValueError("class_fund must be non-negative.")

    popularity_score = compute_ticket_popularity_score(ticket.main_numbers)
    other_winners = estimate_other_winners(
        prize_class=prize_class,
        ticket=ticket,
        tickets_sold=tickets_sold,
        market_model=market_model,
        rng=rng,
    )

    total_winners = 1 + other_winners
    payout = class_fund / total_winners

    return payout, other_winners, popularity_score
