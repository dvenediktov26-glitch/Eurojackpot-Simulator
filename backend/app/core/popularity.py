"""Popularity model for human number selection.

The realistic market mode does not assume that all main numbers are selected
uniformly by other players. Instead, it approximates human preferences using
anchor values from a published lottery-number preference study and a smooth
trend for the remaining numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

# In a 6-from-45 lottery the baseline selection rate for one number is 6/45.
# The cited paper reports deviations from that average for several numbers.
LOTTO45_BASE_SELECTION_RATE = 6 / 45

# Exact anchor values explicitly taken from the source material.
LOTTO45_ANCHOR_SELECTION_RATES: dict[int, float] = {
    7: 0.163,
    11: 0.165,
    37: 0.103,
    38: 0.105,
}

# A small set of numbers used in simple examples and tests.
POPULAR_MAIN_NUMBERS = {7, 11, 13, 21, 23, 42}


@dataclass(frozen=True)
class NumberWeight:
    """One helper record used when inspecting or exporting popularity weights."""

    number: int
    relative_weight: float


def _anchor_relative_weight(selection_rate: float) -> float:
    """Convert an observed selection rate into a relative weight."""
    return selection_rate / LOTTO45_BASE_SELECTION_RATE


def _smooth_base_relative_weight(number: int) -> float:
    """Approximate the baseline popularity trend for numbers 1..45.

    Lower numbers tend to be selected slightly more often and higher numbers a
    bit less often. A linear trend is enough for the current simulation.
    """
    if not 1 <= number <= 45:
        raise ValueError("This smooth profile is defined only for numbers 1..45.")

    start = 1.15
    end = 0.85
    slope = (end - start) / (45 - 1)
    return start + slope * (number - 1)


def _tail_extension_relative_weight(number: int) -> float:
    """Extend the weight profile from 45 numbers to Eurojackpot's 50 numbers."""
    if not 46 <= number <= 50:
        raise ValueError("Tail extension is defined only for numbers 46..50.")

    # Number 45 is around 0.85 in the linear profile, so the extra values keep
    # falling very slightly below that level.
    return 0.85 - 0.01 * (number - 45)


def get_main_number_relative_weights() -> dict[int, float]:
    """Return relative selection weights for all main numbers 1..50.

    These are not probabilities yet. They only describe how popular one number
    is relative to the average number.
    """
    weights: dict[int, float] = {}

    # First create a smooth baseline for the original 1..45 study range.
    for number in range(1, 46):
        weights[number] = _smooth_base_relative_weight(number)

    # Then overwrite a few numbers with exact anchor values taken from the study.
    for number, rate in LOTTO45_ANCHOR_SELECTION_RATES.items():
        weights[number] = _anchor_relative_weight(rate)

    # Finally extend the profile to the 46..50 tail required by Eurojackpot.
    for number in range(46, 51):
        weights[number] = _tail_extension_relative_weight(number)

    return weights


def get_main_number_probabilities() -> dict[int, float]:
    """Normalize relative popularity weights into probabilities."""
    relative_weights = get_main_number_relative_weights()
    total = sum(relative_weights.values())

    if total <= 0:
        raise ValueError("Sum of relative weights must be positive.")

    return {number: weight / total for number, weight in relative_weights.items()}


def get_anti_popular_main_number_probabilities() -> dict[int, float]:
    """Invert the popularity profile to simulate a crowd-avoiding strategy."""
    relative_weights = get_main_number_relative_weights()
    inverted = {number: 1.0 / weight for number, weight in relative_weights.items()}
    total = sum(inverted.values())

    if total <= 0:
        raise ValueError("Sum of inverted weights must be positive.")

    return {number: weight / total for number, weight in inverted.items()}


def get_birthday_main_number_probabilities() -> dict[int, float]:
    """Return a simplified birthday strategy.

    The model assumes that only numbers 1..31 are chosen and that they are
    equally likely inside that range.
    """
    probabilities: dict[int, float] = {}

    for number in range(1, 51):
        probabilities[number] = 1 / 31 if 1 <= number <= 31 else 0.0

    return probabilities


def get_uniform_main_number_probabilities() -> dict[int, float]:
    """Return a fully uniform distribution over all 50 main numbers."""
    return {number: 1 / 50 for number in range(1, 51)}


def compute_ticket_popularity_score(main_numbers: set[int] | frozenset[int]) -> float:
    """Compute how human-like a ticket looks.

    A score above 1.0 means the ticket contains numbers that are selected more
    often than average; a score below 1.0 means the ticket is relatively rare.
    """
    relative_weights = get_main_number_relative_weights()

    if len(main_numbers) != 5:
        raise ValueError("A Eurojackpot ticket must contain exactly 5 main numbers.")

    product = 1.0
    for number in main_numbers:
        if number not in relative_weights:
            raise ValueError(f"Unsupported main number: {number}")
        product *= relative_weights[number]

    # The geometric mean keeps the score interpretable on the same relative
    # scale as the single-number weights.
    return product ** (1 / len(main_numbers))
