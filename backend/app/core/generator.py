from __future__ import annotations

import random

from app.core.config import (
    EURO_NUMBERS_COUNT,
    EURO_NUMBERS_MAX,
    EURO_NUMBERS_MIN,
    MAIN_NUMBERS_COUNT,
    MAIN_NUMBERS_MAX,
    MAIN_NUMBERS_MIN,
)
from app.core.models import Draw, Ticket
from app.core.popularity import (
    get_anti_popular_main_number_probabilities,
    get_birthday_main_number_probabilities,
    get_main_number_probabilities,
    get_uniform_main_number_probabilities,
)

SUPPORTED_STRATEGIES = {"random", "popular", "birthday", "anti_popular"}


def weighted_sample_without_replacement(
    population: list[int],
    weights: list[float],
    k: int,
    rng: random.Random,
) -> list[int]:
    if len(population) != len(weights):
        raise ValueError("Population and weights must have the same length.")

    if k < 0 or k > len(population):
        raise ValueError("Invalid sample size.")

    remaining_population = population[:]
    remaining_weights = weights[:]
    selected: list[int] = []

    for _ in range(k):
        total_weight = sum(remaining_weights)

        if total_weight <= 0:
            raise ValueError("Sum of remaining weights must be positive.")

        threshold = rng.random() * total_weight
        cumulative = 0.0
        chosen_index = 0

        for index, weight in enumerate(remaining_weights):
            cumulative += weight
            if cumulative >= threshold:
                chosen_index = index
                break

        selected.append(remaining_population.pop(chosen_index))
        remaining_weights.pop(chosen_index)

    return selected


def generate_main_numbers_uniform(rng: random.Random) -> frozenset[int]:
    return frozenset(
        rng.sample(range(MAIN_NUMBERS_MIN, MAIN_NUMBERS_MAX + 1), MAIN_NUMBERS_COUNT)
    )


def generate_main_numbers_weighted(
    rng: random.Random,
    probabilities: dict[int, float],
) -> frozenset[int]:
    population = list(range(MAIN_NUMBERS_MIN, MAIN_NUMBERS_MAX + 1))
    weights = [probabilities[number] for number in population]

    return frozenset(
        weighted_sample_without_replacement(
            population=population,
            weights=weights,
            k=MAIN_NUMBERS_COUNT,
            rng=rng,
        )
    )


def generate_euro_numbers(rng: random.Random) -> frozenset[int]:
    return frozenset(
        rng.sample(range(EURO_NUMBERS_MIN, EURO_NUMBERS_MAX + 1), EURO_NUMBERS_COUNT)
    )


def generate_ticket(rng: random.Random, strategy: str = "random") -> Ticket:
    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy}")

    if strategy == "random":
        main_numbers = generate_main_numbers_uniform(rng)
    elif strategy == "popular":
        main_numbers = generate_main_numbers_weighted(
            rng, get_main_number_probabilities()
        )
    elif strategy == "birthday":
        main_numbers = generate_main_numbers_weighted(
            rng, get_birthday_main_number_probabilities()
        )
    elif strategy == "anti_popular":
        main_numbers = generate_main_numbers_weighted(
            rng, get_anti_popular_main_number_probabilities()
        )
    else:
        raise ValueError(f"Unsupported strategy: {strategy}")

    return Ticket(
        main_numbers=main_numbers,
        euro_numbers=generate_euro_numbers(rng),
    )


def generate_draw(rng: random.Random) -> Draw:
    return Draw(
        main_numbers=generate_main_numbers_uniform(rng),
        euro_numbers=generate_euro_numbers(rng),
    )