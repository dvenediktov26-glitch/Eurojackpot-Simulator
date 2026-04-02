"""Tests for ticket and draw generation helpers.

These tests focus on structural correctness: valid ranges, uniqueness, and the
behaviour of weighted strategies.
"""

import random

from app.core.generator import (
    generate_ticket,
    weighted_sample_without_replacement,
)


def test_weighted_sample_without_replacement_returns_unique_values():
    rng = random.Random(42)

    sample = weighted_sample_without_replacement(
        population=[1, 2, 3, 4, 5],
        weights=[1, 1, 1, 1, 1],
        k=3,
        rng=rng,
    )

    assert len(sample) == 3
    assert len(set(sample)) == 3


def test_generate_random_ticket_has_valid_structure():
    rng = random.Random(42)
    ticket = generate_ticket(rng, strategy="random")

    assert len(ticket.main_numbers) == 5
    assert len(ticket.euro_numbers) == 2
    assert all(1 <= n <= 50 for n in ticket.main_numbers)
    assert all(1 <= n <= 12 for n in ticket.euro_numbers)


def test_generate_birthday_ticket_uses_only_1_to_31_for_main_numbers():
    rng = random.Random(42)
    ticket = generate_ticket(rng, strategy="birthday")

    assert all(1 <= n <= 31 for n in ticket.main_numbers)


def test_generate_popular_ticket_has_valid_structure():
    rng = random.Random(42)
    ticket = generate_ticket(rng, strategy="popular")

    assert len(ticket.main_numbers) == 5
    assert len(ticket.euro_numbers) == 2
    assert all(1 <= n <= 50 for n in ticket.main_numbers)


def test_generate_anti_popular_ticket_has_valid_structure():
    rng = random.Random(42)
    ticket = generate_ticket(rng, strategy="anti_popular")

    assert len(ticket.main_numbers) == 5
    assert len(ticket.euro_numbers) == 2
    assert all(1 <= n <= 50 for n in ticket.main_numbers)