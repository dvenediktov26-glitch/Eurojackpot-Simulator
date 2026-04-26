"""Run reproducible experiments for chapter 3.

Run from the backend directory:
    python -m experiments.run_experiments
"""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median, stdev

from app.schemas import SimulationRequest, UserTicketInput
from app.simulator_service import simulate_lottery
from experiments.scenarios import (
    JACKPOT_EXPERIMENT,
    PROFIT_THRESHOLD_SCENARIOS,
    PROFIT_THRESHOLDS_EUR,
    RTP_MARKET_SCENARIOS,
    JackpotExperimentConfig,
)


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(rows: list[dict], output_path: Path) -> None:
    """Write rows to CSV."""
    if not rows:
        return

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def safe_stdev(values: list[float]) -> float:
    """Return standard deviation if defined."""
    if len(values) < 2:
        return 0.0
    return stdev(values)


def build_request(
    draws: int,
    seed: int,
    market_model: str,
    tickets_sold_per_draw: int,
    main_numbers: list[int],
    euro_numbers: list[int],
) -> SimulationRequest:
    """Build a validated simulation request."""
    return SimulationRequest(
        draws=draws,
        seed=seed,
        market_model=market_model,
        tickets_sold_per_draw=tickets_sold_per_draw,
        user_ticket=UserTicketInput(
            main_numbers=main_numbers,
            euro_numbers=euro_numbers,
        ),
    )


def run_profit_threshold_experiments() -> tuple[list[dict], list[dict]]:
    """Experiment 1: probability of reaching positive net-result thresholds."""
    run_rows: list[dict] = []

    print("Experiment 1: pravděpodobnost dosažení kladného výsledku")

    for scenario in PROFIT_THRESHOLD_SCENARIOS:
        print(f"  Scenario: {scenario.name}")

        for repetition_index in range(scenario.repetitions):
            request = build_request(
                draws=scenario.draws,
                seed=scenario.base_seed + repetition_index,
                market_model=scenario.market_model,
                tickets_sold_per_draw=scenario.tickets_sold_per_draw,
                main_numbers=scenario.main_numbers,
                euro_numbers=scenario.euro_numbers,
            )
            result = simulate_lottery(request)

            row = {
                "experiment": "profit_thresholds",
                "scenario": scenario.name,
                "label_cs": scenario.label_cs,
                "description": scenario.description,
                "repeat": repetition_index + 1,
                "seed": request.seed,
                "draws": request.draws,
                "market_model": request.market_model,
                "tickets_sold_per_draw": request.tickets_sold_per_draw,
                "net_result": result.net_result,
                "total_spent": result.total_spent,
                "total_won": result.total_won,
                "rtp": result.rtp,
                "winning_ticket_ratio": result.winning_ticket_ratio,
            }

            for threshold in PROFIT_THRESHOLDS_EUR:
                row[f"net_ge_{threshold}"] = 1 if result.net_result >= threshold else 0

            run_rows.append(row)

        print(f"    completed {scenario.repetitions} repetition(s)")

    summary_rows: list[dict] = []

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in run_rows:
        grouped[row["scenario"]].append(row)

    for scenario_name, rows in grouped.items():
        first = rows[0]
        net_values = [float(row["net_result"]) for row in rows]
        rtp_values = [float(row["rtp"]) for row in rows]
        win_ratio_values = [float(row["winning_ticket_ratio"]) for row in rows]

        summary = {
            "experiment": "profit_thresholds",
            "scenario": scenario_name,
            "label_cs": first["label_cs"],
            "description": first["description"],
            "draws": first["draws"],
            "market_model": first["market_model"],
            "tickets_sold_per_draw": first["tickets_sold_per_draw"],
            "repetitions": len(rows),
            "mean_net_result": mean(net_values),
            "min_net_result": min(net_values),
            "max_net_result": max(net_values),
            "std_net_result": safe_stdev(net_values),
            "mean_rtp": mean(rtp_values),
            "mean_winning_ticket_ratio": mean(win_ratio_values),
        }

        for threshold in PROFIT_THRESHOLDS_EUR:
            hits = sum(int(row[f"net_ge_{threshold}"]) for row in rows)
            summary[f"probability_ge_{threshold}"] = hits / len(rows)

        summary_rows.append(summary)

    return run_rows, summary_rows


def geometric_waiting_time(rng: random.Random, success_probability: float) -> int:
    """Sample number of trials until the first success."""
    u = rng.random()
    return math.floor(math.log(1 - u) / math.log(1 - success_probability)) + 1


def run_jackpot_experiment(config: JackpotExperimentConfig) -> tuple[list[dict], list[dict]]:
    """Experiment 2: waiting time until the first jackpot."""
    rng = random.Random(config.seed)
    run_rows: list[dict] = []

    print("Experiment 2: objem hry potřebný k dosažení jackpotu")

    for repetition_index in range(config.repetitions):
        tickets_until_jackpot = geometric_waiting_time(rng, config.jackpot_probability)
        spent_until_jackpot_eur = tickets_until_jackpot * config.ticket_price_eur
        approx_net_result_eur = config.assumed_jackpot_payout_eur - spent_until_jackpot_eur

        run_rows.append(
            {
                "experiment": "jackpot_waiting_time",
                "scenario": config.name,
                "label_cs": config.label_cs,
                "description": config.description,
                "repeat": repetition_index + 1,
                "tickets_until_jackpot": tickets_until_jackpot,
                "spent_until_jackpot_eur": spent_until_jackpot_eur,
                "assumed_jackpot_payout_eur": config.assumed_jackpot_payout_eur,
                "approx_net_result_eur": approx_net_result_eur,
            }
        )

    tickets_values = [float(row["tickets_until_jackpot"]) for row in run_rows]
    spent_values = [float(row["spent_until_jackpot_eur"]) for row in run_rows]
    net_values = [float(row["approx_net_result_eur"]) for row in run_rows]

    summary_rows = [
        {
            "experiment": "jackpot_waiting_time",
            "scenario": config.name,
            "label_cs": config.label_cs,
            "description": config.description,
            "repetitions": len(run_rows),
            "jackpot_probability": config.jackpot_probability,
            "ticket_price_eur": config.ticket_price_eur,
            "assumed_jackpot_payout_eur": config.assumed_jackpot_payout_eur,
            "mean_tickets_until_jackpot": mean(tickets_values),
            "median_tickets_until_jackpot": median(tickets_values),
            "min_tickets_until_jackpot": min(tickets_values),
            "max_tickets_until_jackpot": max(tickets_values),
            "mean_spent_until_jackpot_eur": mean(spent_values),
            "median_spent_until_jackpot_eur": median(spent_values),
            "mean_approx_net_result_eur": mean(net_values),
            "median_approx_net_result_eur": median(net_values),
            "probability_non_negative_net_result": sum(1 for value in net_values if value >= 0)
            / len(net_values),
        }
    ]

    print(f"    completed {config.repetitions} repetition(s)")
    return run_rows, summary_rows


def run_rtp_market_experiments() -> tuple[list[dict], list[dict]]:
    """Experiment 3: RTP in realistic vs uniform model by market size."""
    run_rows: list[dict] = []

    print("Experiment 3: srovnání RTP podle velikosti trhu")

    for scenario in RTP_MARKET_SCENARIOS:
        print(f"  Scenario: {scenario.name}")

        for repetition_index in range(scenario.repetitions):
            request = build_request(
                draws=scenario.draws,
                seed=scenario.base_seed + repetition_index,
                market_model=scenario.market_model,
                tickets_sold_per_draw=scenario.tickets_sold_per_draw,
                main_numbers=scenario.main_numbers,
                euro_numbers=scenario.euro_numbers,
            )
            result = simulate_lottery(request)

            run_rows.append(
                {
                    "experiment": "rtp_market_comparison",
                    "scenario": scenario.name,
                    "label_cs": scenario.label_cs,
                    "description": scenario.description,
                    "repeat": repetition_index + 1,
                    "seed": request.seed,
                    "draws": request.draws,
                    "market_model": request.market_model,
                    "tickets_sold_per_draw": request.tickets_sold_per_draw,
                    "net_result": result.net_result,
                    "total_spent": result.total_spent,
                    "total_won": result.total_won,
                    "rtp": result.rtp,
                    "winning_ticket_ratio": result.winning_ticket_ratio,
                }
            )

        print(f"    completed {scenario.repetitions} repetition(s)")

    summary_rows: list[dict] = []
    grouped: dict[str, list[dict]] = defaultdict(list)

    for row in run_rows:
        grouped[row["scenario"]].append(row)

    for scenario_name, rows in grouped.items():
        first = rows[0]
        net_values = [float(row["net_result"]) for row in rows]
        rtp_values = [float(row["rtp"]) for row in rows]
        win_ratio_values = [float(row["winning_ticket_ratio"]) for row in rows]

        summary_rows.append(
            {
                "experiment": "rtp_market_comparison",
                "scenario": scenario_name,
                "label_cs": first["label_cs"],
                "description": first["description"],
                "draws": first["draws"],
                "market_model": first["market_model"],
                "tickets_sold_per_draw": first["tickets_sold_per_draw"],
                "repetitions": len(rows),
                "mean_net_result": mean(net_values),
                "std_net_result": safe_stdev(net_values),
                "mean_rtp": mean(rtp_values),
                "std_rtp": safe_stdev(rtp_values),
                "mean_winning_ticket_ratio": mean(win_ratio_values),
            }
        )

    return run_rows, summary_rows


def main() -> None:
    """Run all experiments and save outputs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    profit_run_rows, profit_summary_rows = run_profit_threshold_experiments()
    jackpot_run_rows, jackpot_summary_rows = run_jackpot_experiment(JACKPOT_EXPERIMENT)
    rtp_market_run_rows, rtp_market_summary_rows = run_rtp_market_experiments()

    write_csv(profit_run_rows, RESULTS_DIR / f"experiment1_profit_runs_{timestamp}.csv")
    write_csv(profit_summary_rows, RESULTS_DIR / f"experiment1_profit_summary_{timestamp}.csv")

    write_csv(jackpot_run_rows, RESULTS_DIR / f"experiment2_jackpot_runs_{timestamp}.csv")
    write_csv(jackpot_summary_rows, RESULTS_DIR / f"experiment2_jackpot_summary_{timestamp}.csv")

    write_csv(rtp_market_run_rows, RESULTS_DIR / f"experiment3_rtp_market_runs_{timestamp}.csv")
    write_csv(
        rtp_market_summary_rows,
        RESULTS_DIR / f"experiment3_rtp_market_summary_{timestamp}.csv",
    )

    print("\nAll experiments finished.")
    print(f"Saved CSV files to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()