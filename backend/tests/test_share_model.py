import random

from app.core.models import Ticket
from app.core.share_model import (
    PRIZE_CLASS_PROBABILITIES,
    calculate_shared_payout,
    estimate_lambda_for_ticket,
    sample_poisson,
)


def make_ticket(main_numbers: set[int]) -> Ticket:
    return Ticket(
        main_numbers=frozenset(main_numbers),
        euro_numbers=frozenset({1, 2}),
    )


def test_sample_poisson_zero_lambda_returns_zero():
    rng = random.Random(42)
    assert sample_poisson(0.0, rng) == 0


def test_prize_class_probabilities_exist():
    assert "Class 1" in PRIZE_CLASS_PROBABILITIES
    assert "Class 12" in PRIZE_CLASS_PROBABILITIES
    assert PRIZE_CLASS_PROBABILITIES["Class 12"] > PRIZE_CLASS_PROBABILITIES["Class 1"]


def test_lambda_is_positive_for_valid_ticket():
    ticket = make_ticket({7, 11, 13, 21, 23})

    lam = estimate_lambda_for_ticket(
        prize_class="Class 12",
        ticket=ticket,
        tickets_sold=10_000_000,
        market_model="realistic",
    )

    assert lam > 0


def test_realistic_market_penalizes_popular_ticket_more_than_uniform_market():
    ticket = make_ticket({7, 11, 13, 21, 23})

    uniform_lambda = estimate_lambda_for_ticket(
        prize_class="Class 12",
        ticket=ticket,
        tickets_sold=10_000_000,
        market_model="uniform",
    )
    realistic_lambda = estimate_lambda_for_ticket(
        prize_class="Class 12",
        ticket=ticket,
        tickets_sold=10_000_000,
        market_model="realistic",
    )

    assert realistic_lambda > uniform_lambda


def test_uniform_market_ignores_ticket_popularity():
    popular_ticket = make_ticket({7, 11, 13, 21, 23})
    unpopular_ticket = make_ticket({34, 37, 38, 46, 49})

    popular_lambda = estimate_lambda_for_ticket(
        prize_class="Class 12",
        ticket=popular_ticket,
        tickets_sold=10_000_000,
        market_model="uniform",
    )
    unpopular_lambda = estimate_lambda_for_ticket(
        prize_class="Class 12",
        ticket=unpopular_ticket,
        tickets_sold=10_000_000,
        market_model="uniform",
    )

    assert popular_lambda == unpopular_lambda


def test_payout_is_not_greater_than_class_fund():
    rng = random.Random(42)
    ticket = make_ticket({7, 11, 13, 21, 23})

    payout, other_winners, popularity_score = calculate_shared_payout(
        prize_class="Class 12",
        ticket=ticket,
        class_fund=1000.0,
        tickets_sold=10_000_000,
        market_model="realistic",
        rng=rng,
    )

    assert payout <= 1000.0
    assert other_winners >= 0
    assert popularity_score > 0