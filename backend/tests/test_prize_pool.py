from app.core.prize_pool import (
    CLASS_ALLOCATION_SHARES,
    JACKPOT_CAP,
    PRIZE_POOL_SHARE,
    RESERVE_FUND_SHARE,
    SECOND_TIER_CAP,
    allocate_prize_pool_by_class,
    calculate_prize_pool,
    calculate_ticket_sales,
    validate_class_allocation_shares,
)


def test_class_allocation_shares_sum_to_realistic_total():
    validate_class_allocation_shares(CLASS_ALLOCATION_SHARES)
    assert abs(sum(CLASS_ALLOCATION_SHARES.values()) - 0.91) < 1e-12
    assert abs(sum(CLASS_ALLOCATION_SHARES.values()) + RESERVE_FUND_SHARE - 1.0) < 1e-12


def test_ticket_sales_calculation():
    assert calculate_ticket_sales(10_000_000) == 20_000_000.0


def test_prize_pool_calculation():
    expected = 20_000_000.0 * PRIZE_POOL_SHARE
    assert calculate_prize_pool(10_000_000) == expected


def test_allocate_prize_pool_by_class_preserves_total_with_reserve():
    prize_pool = 10_000_000.0
    class_funds, reserve_fund = allocate_prize_pool_by_class(prize_pool)

    assert abs(sum(class_funds.values()) + reserve_fund - prize_pool) < 1e-9


def test_caps_are_120_million():
    assert JACKPOT_CAP == 120_000_000.0
    assert SECOND_TIER_CAP == 120_000_000.0