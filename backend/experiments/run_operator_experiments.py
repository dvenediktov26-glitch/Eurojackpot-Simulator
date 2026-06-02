"""Run the redesigned operator-focused experiments for chapter 3.

This runner keeps the old player-focused experiment pipeline untouched and adds
new CSV outputs for the thesis redesign:

H2: jackpot-cap sensitivity
H3: prize-structure sensitivity
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

from experiments.operator_model import LotteryDesign, run_operator_simulation
from experiments.operator_scenarios import (
    JACKPOT_CAP_SCENARIOS,
    OPERATOR_EXPERIMENT_CONFIG,
    PRIZE_STRUCTURE_SCENARIOS,
)

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def safe_mean(values: list[float]) -> float:
    """Return a mean value that also works for empty inputs."""
    return mean(values) if values else 0.0


def write_csv(rows: list[dict], path: Path) -> None:
    """Write a list of dictionaries to CSV."""
    if not rows:
        raise ValueError(f"No rows to write for {path.name}.")

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_h2_jackpot_cap_experiment() -> tuple[list[dict], list[dict]]:
    """Run the jackpot-cap sensitivity experiment."""
    run_rows: list[dict] = []
    summary_rows: list[dict] = []

    for scenario_index, scenario in enumerate(JACKPOT_CAP_SCENARIOS):
        for repetition in range(OPERATOR_EXPERIMENT_CONFIG.repetitions):
            seed = OPERATOR_EXPERIMENT_CONFIG.base_seed + scenario_index * 10_000 + repetition
            design = LotteryDesign(
                prize_pool_share=OPERATOR_EXPERIMENT_CONFIG.prize_pool_share,
                reserve_fund_share=OPERATOR_EXPERIMENT_CONFIG.reserve_fund_share,
                jackpot_cap=scenario.jackpot_cap,
                second_tier_cap=scenario.second_tier_cap,
                class_allocation_shares=dict(scenario.class_allocation_shares),
            )
            stats = run_operator_simulation(
                draws=OPERATOR_EXPERIMENT_CONFIG.draws_per_run,
                tickets_sold_per_draw=OPERATOR_EXPERIMENT_CONFIG.tickets_sold_per_draw,
                design=design,
                seed=seed,
            )

            run_rows.append(
                {
                    "experiment": "h2_jackpot_cap",
                    "scenario": scenario.name,
                    "label_cs": scenario.label_cs,
                    "description": scenario.description,
                    "repetition": repetition + 1,
                    "seed": seed,
                    "draws": stats.draws_simulated,
                    "tickets_sold_per_draw": stats.tickets_sold_per_draw,
                    "prize_pool_share": stats.prize_pool_share,
                    "jackpot_cap": stats.jackpot_cap,
                    "total_ticket_sales": stats.total_ticket_sales,
                    "total_prize_pool": stats.total_prize_pool,
                    "total_actual_payout": stats.total_actual_payout,
                    "total_actual_upper_tier_payout": stats.total_actual_upper_tier_payout,
                    "jackpot_hits": stats.jackpot_hits,
                    "jackpot_cap_hits": stats.jackpot_cap_hits,
                    "cap_reach_count": stats.cap_reach_count,
                    "total_overflow_to_class2": stats.total_overflow_to_class2,
                    "total_overflow_to_class3": stats.total_overflow_to_class3,
                    "max_jackpot_fund_observed": stats.max_jackpot_fund_observed,
                    "final_jackpot_carryover": stats.final_jackpot_carryover,
                    "average_jackpot_available": stats.average_jackpot_available,
                    "average_total_payout": stats.average_total_payout,
                    "payout_std_dev": stats.payout_std_dev,
                    "upper_tier_payout_std_dev": stats.upper_tier_payout_std_dev,
                    "average_rollover_length": stats.average_rollover_length,
                    "longest_rollover_length": stats.longest_rollover_length,
                    "average_time_to_cap": stats.average_time_to_cap,
                }
            )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in run_rows:
        grouped[row["scenario"]].append(row)

    for scenario in JACKPOT_CAP_SCENARIOS:
        rows = grouped[scenario.name]
        summary_rows.append(
            {
                "experiment": "h2_jackpot_cap",
                "scenario": scenario.name,
                "label_cs": scenario.label_cs,
                "description": scenario.description,
                "jackpot_cap": rows[0]["jackpot_cap"],
                "draws": rows[0]["draws"],
                "repetitions": len(rows),
                "mean_average_jackpot_available": safe_mean(
                    [float(row["average_jackpot_available"]) for row in rows]
                ),
                "mean_max_jackpot_fund_observed": safe_mean(
                    [float(row["max_jackpot_fund_observed"]) for row in rows]
                ),
                "mean_payout_std_dev": safe_mean(
                    [float(row["payout_std_dev"]) for row in rows]
                ),
                "mean_upper_tier_payout_std_dev": safe_mean(
                    [float(row["upper_tier_payout_std_dev"]) for row in rows]
                ),
                "mean_average_rollover_length": safe_mean(
                    [float(row["average_rollover_length"]) for row in rows]
                ),
                "mean_average_time_to_cap": safe_mean(
                    [float(row["average_time_to_cap"]) for row in rows]
                ),
                "mean_jackpot_hits": safe_mean([float(row["jackpot_hits"]) for row in rows]),
                "mean_jackpot_cap_hits": safe_mean(
                    [float(row["jackpot_cap_hits"]) for row in rows]
                ),
                "mean_overflow_to_class2": safe_mean(
                    [float(row["total_overflow_to_class2"]) for row in rows]
                ),
                "mean_overflow_to_class3": safe_mean(
                    [float(row["total_overflow_to_class3"]) for row in rows]
                ),
            }
        )

    return run_rows, summary_rows


def run_h3_prize_structure_experiment() -> tuple[list[dict], list[dict]]:
    """Run the prize-structure sensitivity experiment."""
    run_rows: list[dict] = []
    summary_rows: list[dict] = []

    for scenario_index, scenario in enumerate(PRIZE_STRUCTURE_SCENARIOS):
        for repetition in range(OPERATOR_EXPERIMENT_CONFIG.repetitions):
            seed = OPERATOR_EXPERIMENT_CONFIG.base_seed + 100_000 + scenario_index * 10_000 + repetition
            design = LotteryDesign(
                prize_pool_share=OPERATOR_EXPERIMENT_CONFIG.prize_pool_share,
                reserve_fund_share=OPERATOR_EXPERIMENT_CONFIG.reserve_fund_share,
                jackpot_cap=scenario.jackpot_cap,
                second_tier_cap=scenario.second_tier_cap,
                class_allocation_shares=dict(scenario.class_allocation_shares),
            )
            stats = run_operator_simulation(
                draws=OPERATOR_EXPERIMENT_CONFIG.draws_per_run,
                tickets_sold_per_draw=OPERATOR_EXPERIMENT_CONFIG.tickets_sold_per_draw,
                design=design,
                seed=seed,
            )

            run_rows.append(
                {
                    "experiment": "h3_prize_structure",
                    "scenario": scenario.name,
                    "label_cs": scenario.label_cs,
                    "description": scenario.description,
                    "repetition": repetition + 1,
                    "seed": seed,
                    "draws": stats.draws_simulated,
                    "tickets_sold_per_draw": stats.tickets_sold_per_draw,
                    "prize_pool_share": stats.prize_pool_share,
                    "jackpot_cap": stats.jackpot_cap,
                    "jackpot_share": design.class_allocation_shares["Class 1"],
                    "class11_share": design.class_allocation_shares["Class 11"],
                    "class12_share": design.class_allocation_shares["Class 12"],
                    "total_ticket_sales": stats.total_ticket_sales,
                    "total_prize_pool": stats.total_prize_pool,
                    "total_actual_payout": stats.total_actual_payout,
                    "total_actual_upper_tier_payout": stats.total_actual_upper_tier_payout,
                    "jackpot_hits": stats.jackpot_hits,
                    "jackpot_cap_hits": stats.jackpot_cap_hits,
                    "cap_reach_count": stats.cap_reach_count,
                    "total_overflow_to_class2": stats.total_overflow_to_class2,
                    "total_overflow_to_class3": stats.total_overflow_to_class3,
                    "max_jackpot_fund_observed": stats.max_jackpot_fund_observed,
                    "final_jackpot_carryover": stats.final_jackpot_carryover,
                    "average_jackpot_available": stats.average_jackpot_available,
                    "average_total_payout": stats.average_total_payout,
                    "payout_std_dev": stats.payout_std_dev,
                    "upper_tier_payout_std_dev": stats.upper_tier_payout_std_dev,
                    "average_rollover_length": stats.average_rollover_length,
                    "longest_rollover_length": stats.longest_rollover_length,
                    "average_time_to_cap": stats.average_time_to_cap,
                }
            )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in run_rows:
        grouped[row["scenario"]].append(row)

    for scenario in PRIZE_STRUCTURE_SCENARIOS:
        rows = grouped[scenario.name]
        summary_rows.append(
            {
                "experiment": "h3_prize_structure",
                "scenario": scenario.name,
                "label_cs": scenario.label_cs,
                "description": scenario.description,
                "jackpot_share": rows[0]["jackpot_share"],
                "draws": rows[0]["draws"],
                "repetitions": len(rows),
                "mean_average_jackpot_available": safe_mean(
                    [float(row["average_jackpot_available"]) for row in rows]
                ),
                "mean_max_jackpot_fund_observed": safe_mean(
                    [float(row["max_jackpot_fund_observed"]) for row in rows]
                ),
                "mean_payout_std_dev": safe_mean(
                    [float(row["payout_std_dev"]) for row in rows]
                ),
                "mean_upper_tier_payout_std_dev": safe_mean(
                    [float(row["upper_tier_payout_std_dev"]) for row in rows]
                ),
                "mean_average_rollover_length": safe_mean(
                    [float(row["average_rollover_length"]) for row in rows]
                ),
                "mean_average_time_to_cap": safe_mean(
                    [float(row["average_time_to_cap"]) for row in rows]
                ),
                "mean_jackpot_hits": safe_mean([float(row["jackpot_hits"]) for row in rows]),
                "mean_jackpot_cap_hits": safe_mean(
                    [float(row["jackpot_cap_hits"]) for row in rows]
                ),
                "mean_overflow_to_class2": safe_mean(
                    [float(row["total_overflow_to_class2"]) for row in rows]
                ),
                "mean_overflow_to_class3": safe_mean(
                    [float(row["total_overflow_to_class3"]) for row in rows]
                ),
            }
        )

    return run_rows, summary_rows


def main() -> None:
    """Run the new operator-focused chapter 3 experiments."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    h2_run_rows, h2_summary_rows = run_h2_jackpot_cap_experiment()
    h3_run_rows, h3_summary_rows = run_h3_prize_structure_experiment()

    write_csv(h2_run_rows, RESULTS_DIR / f"h2_jackpot_cap_runs_{timestamp}.csv")
    write_csv(h2_summary_rows, RESULTS_DIR / f"h2_jackpot_cap_summary_{timestamp}.csv")

    write_csv(h3_run_rows, RESULTS_DIR / f"h3_prize_structure_runs_{timestamp}.csv")
    write_csv(h3_summary_rows, RESULTS_DIR / f"h3_prize_structure_summary_{timestamp}.csv")

    print("\nOperator experiments finished.")
    print(f"Saved CSV files to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()