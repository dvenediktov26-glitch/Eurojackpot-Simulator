"""Prize-pool construction and allocation rules.

This file converts ticket sales into a prize pool, splits that pool between the
12 prize classes, and exposes jackpot-cap constants used by the main
simulation.
"""

from __future__ import annotations

from app.core.config import TICKET_PRICE_EUR

# The model assumes that 50% of ticket sales are returned to players.
PRIZE_POOL_SHARE = 0.50

# Public Eurojackpot information states a 120 million EUR cap for the jackpot.
JACKPOT_CAP = 120_000_000.0
SECOND_TIER_CAP = 120_000_000.0

# Allocation shares are based on public Eurojackpot prize-fund percentages.
# The 12 listed prize classes consume 91% of the prize pool.
CLASS_ALLOCATION_SHARES: dict[str, float] = {
    "Class 1": 0.36,    # 5 + 2
    "Class 2": 0.086,   # 5 + 1
    "Class 3": 0.0485,  # 5 + 0
    "Class 4": 0.008,   # 4 + 2
    "Class 5": 0.01,    # 4 + 1
    "Class 6": 0.011,   # 3 + 2
    "Class 7": 0.008,   # 4 + 0
    "Class 8": 0.0255,  # 2 + 2
    "Class 9": 0.0285,  # 3 + 1
    "Class 10": 0.054,  # 3 + 0
    "Class 11": 0.0675, # 1 + 2
    "Class 12": 0.203,  # 2 + 1
}

# The remaining 9% is tracked as a reserve / booster fund in this model.
RESERVE_FUND_SHARE = 0.09


def validate_class_allocation_shares(shares: dict[str, float]) -> None:
    """Validate that class shares match the intended realistic model."""
    total = sum(shares.values())

    if abs(total - 0.91) > 1e-12:
        raise ValueError(f"Class allocation shares must sum to 0.91, got {total}.")

    for key, value in shares.items():
        if value < 0:
            raise ValueError(f"Share for {key} must be non-negative.")

    if RESERVE_FUND_SHARE < 0:
        raise ValueError("Reserve fund share must be non-negative.")

    if abs(total + RESERVE_FUND_SHARE - 1.0) > 1e-12:
        raise ValueError("Class shares plus reserve fund share must sum to 1.0.")


def calculate_ticket_sales(tickets_sold_per_draw: int) -> float:
    """Convert the number of sold tickets into gross ticket revenue."""
    if tickets_sold_per_draw < 0:
        raise ValueError("tickets_sold_per_draw must be non-negative.")

    return tickets_sold_per_draw * TICKET_PRICE_EUR


def calculate_prize_pool(
    tickets_sold_per_draw: int,
    prize_pool_share: float = PRIZE_POOL_SHARE,
) -> float:
    """Calculate the total amount available for prizes in one draw."""
    if not 0 <= prize_pool_share <= 1:
        raise ValueError("prize_pool_share must be between 0 and 1.")

    ticket_sales = calculate_ticket_sales(tickets_sold_per_draw)
    return ticket_sales * prize_pool_share


def allocate_prize_pool_by_class(
    prize_pool: float,
    class_allocation_shares: dict[str, float] = CLASS_ALLOCATION_SHARES,
) -> tuple[dict[str, float], float]:
    """Split one draw's prize pool into class funds plus the reserve fund."""
    if prize_pool < 0:
        raise ValueError("prize_pool must be non-negative.")

    validate_class_allocation_shares(class_allocation_shares)

    class_funds = {
        prize_class: prize_pool * share
        for prize_class, share in class_allocation_shares.items()
    }
    reserve_fund = prize_pool * RESERVE_FUND_SHARE

    return class_funds, reserve_fund
