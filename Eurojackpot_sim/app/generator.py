import random
from app.config import (
    MAIN_NUMBERS_COUNT,
    MAIN_NUMBERS_MIN,
    MAIN_NUMBERS_MAX,
    EURO_NUMBERS_COUNT,
    EURO_NUMBERS_MIN,
    EURO_NUMBERS_MAX,
)
from app.models import Ticket, Draw


def generate_main_numbers(rng: random.Random) -> frozenset[int]:
    return frozenset(
        rng.sample(range(MAIN_NUMBERS_MIN, MAIN_NUMBERS_MAX + 1), MAIN_NUMBERS_COUNT)
    )


def generate_euro_numbers(rng: random.Random) -> frozenset[int]:
    return frozenset(
        rng.sample(range(EURO_NUMBERS_MIN, EURO_NUMBERS_MAX + 1), EURO_NUMBERS_COUNT)
    )


def generate_ticket(rng: random.Random) -> Ticket:
    return Ticket(
        main_numbers=generate_main_numbers(rng),
        euro_numbers=generate_euro_numbers(rng),
    )


def generate_draw(rng: random.Random) -> Draw:
    return Draw(
        main_numbers=generate_main_numbers(rng),
        euro_numbers=generate_euro_numbers(rng),
    )