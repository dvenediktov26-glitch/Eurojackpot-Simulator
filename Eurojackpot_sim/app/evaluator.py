"""Legacy ticket evaluation logic used by the console prototype."""

from app.models import Ticket, Draw, EvaluationResult
from app.rules import PRIZE_CLASSES


def evaluate_ticket(ticket: Ticket, draw: Draw) -> EvaluationResult:
    matched_main = len(ticket.main_numbers & draw.main_numbers)
    matched_euro = len(ticket.euro_numbers & draw.euro_numbers)

    prize_class = PRIZE_CLASSES.get((matched_main, matched_euro))

    return EvaluationResult(
        matched_main=matched_main,
        matched_euro=matched_euro,
        prize_class=prize_class,
    )