from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UserTicketInput(BaseModel):
    main_numbers: list[int] = Field(..., min_length=5, max_length=5)
    euro_numbers: list[int] = Field(..., min_length=2, max_length=2)

    @field_validator("main_numbers")
    @classmethod
    def validate_main_numbers(cls, value: list[int]) -> list[int]:
        if len(set(value)) != 5:
            raise ValueError("Main numbers must be unique.")
        if any(number < 1 or number > 50 for number in value):
            raise ValueError("Main numbers must be between 1 and 50.")
        return value

    @field_validator("euro_numbers")
    @classmethod
    def validate_euro_numbers(cls, value: list[int]) -> list[int]:
        if len(set(value)) != 2:
            raise ValueError("Euro numbers must be unique.")
        if any(number < 1 or number > 12 for number in value):
            raise ValueError("Euro numbers must be between 1 and 12.")
        return value


class SimulationRequest(BaseModel):
    draws: int = Field(..., ge=1, le=5_000_000)
    seed: int | None = None
    market_model: Literal["uniform", "realistic"] = "uniform"
    tickets_sold_per_draw: int = Field(10_000_000, ge=1)
    user_ticket: UserTicketInput


class PrizeClassSummary(BaseModel):
    key: str
    label: str
    count: int
    average_class_fund: float
    average_actual_payout: float
    actual_total_won: float


class SimulationResponse(BaseModel):
    draws_simulated: int
    tickets_played: int
    winning_tickets: int
    winning_ticket_ratio: float
    total_spent: float
    total_won: float
    net_result: float
    rtp: float
    market_model_used: str
    tickets_sold_per_draw: int
    average_ticket_popularity: float
    user_ticket: UserTicketInput
    prize_pool_share: float
    total_ticket_sales: float
    total_prize_pool: float
    average_ticket_sales_per_draw: float
    average_prize_pool_per_draw: float
    average_reserve_fund_per_draw: float
    jackpot_hits: int
    jackpot_cap: float
    max_jackpot_fund_observed: float
    final_jackpot_carryover: float
    average_jackpot_carryover_per_draw: float
    average_jackpot_available_per_draw: float
    total_jackpot_overflow_to_class2: float
    total_class2_overflow_to_class3: float
    prize_class_counts: dict[str, int]
    prize_classes: list[PrizeClassSummary]