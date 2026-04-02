"""Tests for exact combinatorial odds.

The goal is to verify that the probability table is internally consistent and
that jackpot odds remain the rarest outcome.
"""

from app.core.odds import get_prize_class_probabilities


def test_prize_class_probabilities_are_positive():
    probabilities = get_prize_class_probabilities()

    assert all(value > 0 for value in probabilities.values())


def test_jackpot_probability_is_smallest():
    probabilities = get_prize_class_probabilities()

    jackpot = probabilities["Class 1"]
    assert all(jackpot <= value for value in probabilities.values())


def test_total_winning_probability_is_less_than_one():
    probabilities = get_prize_class_probabilities()

    assert sum(probabilities.values()) < 1.0