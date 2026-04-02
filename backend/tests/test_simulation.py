from app.core.models import Ticket
from app.core.prize_pool import PRIZE_POOL_SHARE, calculate_prize_pool, calculate_ticket_sales
from app.core.simulation import run_simulation


def make_ticket() -> Ticket:
    return Ticket(
        main_numbers=frozenset({7, 11, 13, 21, 23}),
        euro_numbers=frozenset({1, 2}),
    )


def test_simulation_returns_valid_stats():
    stats = run_simulation(
        n_draws=1000,
        user_ticket=make_ticket(),
        seed=42,
        market_model="uniform",
        tickets_sold_per_draw=10_000_000,
    )

    assert stats.draws_simulated == 1000
    assert stats.tickets_played == 1000
    assert stats.total_spent == 2000.0
    assert stats.total_won >= 0.0
    assert stats.tickets_sold_per_draw == 10_000_000
    assert stats.total_ticket_sales == 1000 * calculate_ticket_sales(10_000_000)
    assert stats.total_prize_pool == 1000 * calculate_prize_pool(10_000_000)
    assert stats.prize_pool_share == PRIZE_POOL_SHARE


def test_simulation_with_same_seed_is_reproducible():
    stats_1 = run_simulation(
        n_draws=2000,
        user_ticket=make_ticket(),
        seed=123,
        market_model="realistic",
        tickets_sold_per_draw=5_000_000,
    )
    stats_2 = run_simulation(
        n_draws=2000,
        user_ticket=make_ticket(),
        seed=123,
        market_model="realistic",
        tickets_sold_per_draw=5_000_000,
    )

    assert stats_1.total_won == stats_2.total_won
    assert stats_1.winning_tickets == stats_2.winning_tickets
    assert stats_1.prize_class_counts == stats_2.prize_class_counts
    assert stats_1.final_jackpot_carryover == stats_2.final_jackpot_carryover
    assert stats_1.total_jackpot_overflow_to_class2 == stats_2.total_jackpot_overflow_to_class2


def test_actual_total_by_class_matches_total_won():
    stats = run_simulation(
        n_draws=3000,
        user_ticket=make_ticket(),
        seed=7,
        market_model="realistic",
        tickets_sold_per_draw=10_000_000,
    )

    summed = sum(stats.actual_total_won_by_class.values())
    assert abs(summed - stats.total_won) < 1e-9


def test_rtp_is_positive_and_bounded():
    stats = run_simulation(
        n_draws=50_000,
        user_ticket=make_ticket(),
        seed=2026,
        market_model="uniform",
        tickets_sold_per_draw=10_000_000,
    )

    assert stats.rtp > 0.0
    assert stats.rtp < 1.0


def test_jackpot_respects_cap():
    stats = run_simulation(
        n_draws=200,
        user_ticket=make_ticket(),
        seed=555,
        market_model="uniform",
        tickets_sold_per_draw=10_000_000,
    )

    assert stats.max_jackpot_fund_observed <= stats.jackpot_cap + 1e-9