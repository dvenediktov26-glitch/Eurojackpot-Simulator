from app.core.models import Ticket
from app.core.simulation import run_simulation
from app.schemas import (
    PrizeClassSummary,
    SimulationRequest,
    SimulationResponse,
    UserTicketInput,
)

PRIZE_CLASS_DEFINITIONS = [
    {"key": "Class 1", "label": "5 + 2 (Jackpot)"},
    {"key": "Class 2", "label": "5 + 1"},
    {"key": "Class 3", "label": "5 + 0"},
    {"key": "Class 4", "label": "4 + 2"},
    {"key": "Class 5", "label": "4 + 1"},
    {"key": "Class 6", "label": "3 + 2"},
    {"key": "Class 7", "label": "4 + 0"},
    {"key": "Class 8", "label": "2 + 2"},
    {"key": "Class 9", "label": "3 + 1"},
    {"key": "Class 10", "label": "3 + 0"},
    {"key": "Class 11", "label": "1 + 2"},
    {"key": "Class 12", "label": "2 + 1"},
]


def _to_ticket(ticket_input: UserTicketInput) -> Ticket:
    return Ticket(
        main_numbers=frozenset(ticket_input.main_numbers),
        euro_numbers=frozenset(ticket_input.euro_numbers),
    )


def simulate_lottery(payload: SimulationRequest) -> SimulationResponse:
    user_ticket = _to_ticket(payload.user_ticket)

    stats = run_simulation(
        n_draws=payload.draws,
        user_ticket=user_ticket,
        seed=payload.seed,
        market_model=payload.market_model,
        tickets_sold_per_draw=payload.tickets_sold_per_draw,
    )

    prize_classes: list[PrizeClassSummary] = []

    for item in PRIZE_CLASS_DEFINITIONS:
        key = item["key"]
        label = item["label"]

        count = stats.prize_class_counts.get(key, 0)
        actual_total_won = stats.actual_total_won_by_class.get(key, 0.0)
        total_class_fund = stats.total_class_fund_by_class.get(key, 0.0)

        average_class_fund = (
            total_class_fund / stats.draws_simulated if stats.draws_simulated > 0 else 0.0
        )
        average_actual_payout = actual_total_won / count if count > 0 else 0.0

        prize_classes.append(
            PrizeClassSummary(
                key=key,
                label=label,
                count=count,
                average_class_fund=average_class_fund,
                average_actual_payout=average_actual_payout,
                actual_total_won=actual_total_won,
            )
        )

    return SimulationResponse(
        draws_simulated=stats.draws_simulated,
        tickets_played=stats.tickets_played,
        winning_tickets=stats.winning_tickets,
        winning_ticket_ratio=stats.winning_ticket_ratio,
        total_spent=stats.total_spent,
        total_won=stats.total_won,
        net_result=stats.net_result,
        rtp=stats.rtp,
        market_model_used=payload.market_model,
        tickets_sold_per_draw=stats.tickets_sold_per_draw,
        average_ticket_popularity=stats.average_ticket_popularity,
        user_ticket=payload.user_ticket,
        prize_pool_share=stats.prize_pool_share,
        total_ticket_sales=stats.total_ticket_sales,
        total_prize_pool=stats.total_prize_pool,
        average_ticket_sales_per_draw=stats.average_ticket_sales_per_draw,
        average_prize_pool_per_draw=stats.average_prize_pool_per_draw,
        average_reserve_fund_per_draw=stats.average_reserve_fund_per_draw,
        jackpot_hits=stats.jackpot_hits,
        jackpot_cap=stats.jackpot_cap,
        max_jackpot_fund_observed=stats.max_jackpot_fund_observed,
        final_jackpot_carryover=stats.final_jackpot_carryover,
        average_jackpot_carryover_per_draw=stats.average_jackpot_carryover_per_draw,
        average_jackpot_available_per_draw=stats.average_jackpot_available_per_draw,
        total_jackpot_overflow_to_class2=stats.total_jackpot_overflow_to_class2,
        total_class2_overflow_to_class3=stats.total_class2_overflow_to_class3,
        prize_class_counts=stats.prize_class_counts,
        prize_classes=prize_classes,
    )