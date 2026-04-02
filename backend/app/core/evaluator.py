"""Ticket evaluation helpers.

This module contains the simplest part of the backend logic: compare one ticket
against one draw and compute the resulting prize class.
"""

from app.core.models import Draw, EvaluationResult, Ticket
from app.core.rules import PRIZE_CLASSES


def evaluate_ticket(ticket: Ticket, draw: Draw) -> EvaluationResult:
    """Compare a ticket with a draw and return the full matching result.

    The set intersection counts how many numbers overlap. The prize class lookup
    is then delegated to the static rule table defined in rules.py.
    """
    # Count how many main numbers and euro numbers were matched.
    matched_main = len(ticket.main_numbers & draw.main_numbers)
    matched_euro = len(ticket.euro_numbers & draw.euro_numbers)

    # Not every match pattern is a winning pattern, so .get() may return None.
    prize_class = PRIZE_CLASSES.get((matched_main, matched_euro))

    return EvaluationResult(
        matched_main=matched_main,
        matched_euro=matched_euro,
        prize_class=prize_class,
    )
