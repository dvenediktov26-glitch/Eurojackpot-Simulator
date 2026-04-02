"""Legacy simulation loop from the original command-line version."""

import random
from collections import Counter

from app.config import TICKET_PRICE_EUR
from app.generator import generate_draw, generate_ticket
from app.evaluator import evaluate_ticket
from app.statistics import SimulationStats


def run_simulation(
    n_draws: int,
    seed: int | None = None,
    prize_amounts: dict[str, float] | None = None,
) -> SimulationStats:
    rng = random.Random(seed)
    prize_amounts = prize_amounts or {}

    prize_class_counts: Counter[str] = Counter()
    winning_tickets = 0
    total_won = 0.0

    for _ in range(n_draws):
        ticket = generate_ticket(rng)
        draw = generate_draw(rng)

        result = evaluate_ticket(ticket, draw)

        if result.prize_class is not None:
            winning_tickets += 1
            prize_class_counts[result.prize_class] += 1
            total_won += prize_amounts.get(result.prize_class, 0.0)

    total_spent = n_draws * TICKET_PRICE_EUR

    return SimulationStats(
        draws_simulated=n_draws,
        tickets_played=n_draws,
        winning_tickets=winning_tickets,
        prize_class_counts=dict(prize_class_counts),
        total_spent=total_spent,
        total_won=total_won,
    )