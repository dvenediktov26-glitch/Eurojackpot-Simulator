"""Exact combinatorial odds for each Eurojackpot prize class.

These probabilities are used in the shared prize model to estimate how many
other winners are likely to exist in the same draw.
"""

from __future__ import annotations

from math import comb

# Eurojackpot draws 5 main numbers from 50 and 2 euro numbers from 12.
TOTAL_MAIN_NUMBERS = 50
DRAWN_MAIN_NUMBERS = 5

TOTAL_EURO_NUMBERS = 12
DRAWN_EURO_NUMBERS = 2

# Prize classes are expressed as (matched_main, matched_euro).
PRIZE_CLASS_MATCHES: dict[str, tuple[int, int]] = {
    "Class 1": (5, 2),
    "Class 2": (5, 1),
    "Class 3": (5, 0),
    "Class 4": (4, 2),
    "Class 5": (4, 1),
    "Class 6": (3, 2),
    "Class 7": (4, 0),
    "Class 8": (2, 2),
    "Class 9": (3, 1),
    "Class 10": (3, 0),
    "Class 11": (1, 2),
    "Class 12": (2, 1),
}


def calculate_match_probability(matched_main: int, matched_euro: int) -> float:
    """Return the exact probability of one match pattern.

    The formula multiplies the number of possible ways to hit the required main
    numbers and euro numbers and divides by the total number of possible tickets.
    """
    # Choose the requested number of hits from the drawn numbers and the rest
    # from the numbers that were not drawn.
    main_ways = comb(DRAWN_MAIN_NUMBERS, matched_main) * comb(
        TOTAL_MAIN_NUMBERS - DRAWN_MAIN_NUMBERS,
        DRAWN_MAIN_NUMBERS - matched_main,
    )
    euro_ways = comb(DRAWN_EURO_NUMBERS, matched_euro) * comb(
        TOTAL_EURO_NUMBERS - DRAWN_EURO_NUMBERS,
        DRAWN_EURO_NUMBERS - matched_euro,
    )

    total_main = comb(TOTAL_MAIN_NUMBERS, DRAWN_MAIN_NUMBERS)
    total_euro = comb(TOTAL_EURO_NUMBERS, DRAWN_EURO_NUMBERS)

    return (main_ways / total_main) * (euro_ways / total_euro)


def get_prize_class_probabilities() -> dict[str, float]:
    """Build a lookup table with the probability of every prize class."""
    return {
        prize_class: calculate_match_probability(matched_main, matched_euro)
        for prize_class, (matched_main, matched_euro) in PRIZE_CLASS_MATCHES.items()
    }
