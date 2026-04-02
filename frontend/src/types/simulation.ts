/**
 * Shared TypeScript types that mirror the backend API schemas.
 *
 * Keeping these interfaces aligned with the FastAPI response models helps the
 * frontend catch breaking API changes during development.
 */

export interface UserTicketInput {
  main_numbers: number[];
  euro_numbers: number[];
}

export interface SimulationRequest {
  draws: number;
  seed?: number | null;
  market_model?: "uniform" | "realistic";
  tickets_sold_per_draw?: number;
  user_ticket: UserTicketInput;
}

export interface PrizeClassSummary {
  key: string;
  label: string;
  count: number;
  average_class_fund: number;
  average_actual_payout: number;
  actual_total_won: number;
}

export interface SimulationResponse {
  draws_simulated: number;
  tickets_played: number;
  winning_tickets: number;
  winning_ticket_ratio: number;
  total_spent: number;
  total_won: number;
  net_result: number;
  rtp: number;
  market_model_used: string;
  tickets_sold_per_draw: number;
  average_ticket_popularity: number;
  user_ticket: UserTicketInput;
  prize_pool_share: number;
  total_ticket_sales: number;
  total_prize_pool: number;
  average_ticket_sales_per_draw: number;
  average_prize_pool_per_draw: number;
  average_reserve_fund_per_draw: number;
  jackpot_hits: number;
  jackpot_cap: number;
  max_jackpot_fund_observed: number;
  final_jackpot_carryover: number;
  average_jackpot_carryover_per_draw: number;
  average_jackpot_available_per_draw: number;
  total_jackpot_overflow_to_class2: number;
  total_class2_overflow_to_class3: number;
  prize_class_counts: Record<string, number>;
  prize_classes: PrizeClassSummary[];
}