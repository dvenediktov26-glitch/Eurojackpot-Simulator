"""Tests for the human-number popularity model.

The popularity model is central to the realistic market mode, so these tests
check normalization, inversion, and expected ordering.
"""

from app.core.popularity import (
    LOTTO45_BASE_SELECTION_RATE,
    compute_ticket_popularity_score,
    get_anti_popular_main_number_probabilities,
    get_birthday_main_number_probabilities,
    get_main_number_probabilities,
    get_main_number_relative_weights,
    get_uniform_main_number_probabilities,
)


def test_lotto45_base_selection_rate():
    assert LOTTO45_BASE_SELECTION_RATE == 6 / 45


def test_main_number_relative_weights_have_all_numbers():
    weights = get_main_number_relative_weights()

    assert len(weights) == 50
    assert set(weights.keys()) == set(range(1, 51))


def test_anchor_numbers_follow_paper_direction():
    weights = get_main_number_relative_weights()

    assert weights[11] > 1.0
    assert weights[7] > 1.0
    assert weights[37] < 1.0
    assert weights[38] < 1.0


def test_11_is_more_popular_than_37():
    weights = get_main_number_relative_weights()

    assert weights[11] > weights[37]


def test_tail_extension_makes_highest_numbers_less_popular():
    weights = get_main_number_relative_weights()

    assert weights[46] < 1.0
    assert weights[50] < weights[46]


def test_main_number_probabilities_are_normalized():
    probabilities = get_main_number_probabilities()

    assert abs(sum(probabilities.values()) - 1.0) < 1e-12


def test_uniform_probabilities_are_normalized():
    probabilities = get_uniform_main_number_probabilities()

    assert abs(sum(probabilities.values()) - 1.0) < 1e-12
    assert probabilities[1] == probabilities[50]


def test_birthday_probabilities_use_only_1_to_31():
    probabilities = get_birthday_main_number_probabilities()

    assert abs(sum(probabilities.values()) - 1.0) < 1e-12
    assert probabilities[1] > 0.0
    assert probabilities[31] > 0.0
    assert probabilities[32] == 0.0
    assert probabilities[50] == 0.0


def test_anti_popular_probabilities_are_normalized():
    probabilities = get_anti_popular_main_number_probabilities()

    assert abs(sum(probabilities.values()) - 1.0) < 1e-12


def test_anti_popular_inverts_preference():
    popular = get_main_number_probabilities()
    anti_popular = get_anti_popular_main_number_probabilities()

    assert popular[11] > popular[37]
    assert anti_popular[11] < anti_popular[37]


def test_popularity_score_prefers_human_like_ticket():
    human_like_ticket = frozenset({7, 11, 13, 21, 23})
    less_popular_ticket = frozenset({34, 37, 38, 46, 49})

    assert (
        compute_ticket_popularity_score(human_like_ticket)
        > compute_ticket_popularity_score(less_popular_ticket)
    )