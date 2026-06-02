"""Run H1 experiment: coverage gap and rollover acceleration.

Run from the backend directory:
    python -m experiments.run_h1_coverage_experiment
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

from experiments.h1_coverage_model import run_h1_coverage_simulation
from experiments.h1_coverage_scenarios import (
    DATE_ONLY_JACKPOT_COMBINATIONS,
    H1_COVERAGE_CONFIG,
    H1_COVERAGE_SCENARIOS,
    POPULAR_EXACT_TICKET_LABELS,
    TOTAL_JACKPOT_COMBINATIONS,
)

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        raise ValueError(f"No rows to write for {path.name}.")

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_summary_rows(run_rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in run_rows:
        grouped[row["scenario"]].append(row)

    summary_rows: list[dict] = []

    for scenario in H1_COVERAGE_SCENARIOS:
        rows = grouped[scenario.name]
        if not rows:
            continue

        summary_rows.append(
            {
                "experiment": "h1_coverage_gap",
                "scenario": scenario.name,
                "label_cs": scenario.label_cs,
                "description": scenario.description,
                "draws_per_run": rows[0]["draws_per_run"],
                "repetitions": len(rows),
                "tickets_sold_per_draw": rows[0]["tickets_sold_per_draw"],
                "uniform_share": rows[0]["uniform_share"],
                "date_only_share": rows[0]["date_only_share"],
                "popular_share": rows[0]["popular_share"],
                "expected_unique_coverage": rows[0]["expected_unique_coverage"],
                "coverage_ratio": rows[0]["coverage_ratio"],
                "jackpot_hit_probability": rows[0]["jackpot_hit_probability"],
                "no_jackpot_winner_probability": rows[0]["no_jackpot_winner_probability"],
                "expected_draws_until_jackpot_hit": rows[0]["expected_draws_until_jackpot_hit"],
                "exact_ticket_hhi": rows[0]["exact_ticket_hhi"],
                "effective_ticket_support": rows[0]["effective_ticket_support"],
                "max_exact_ticket_probability": rows[0]["max_exact_ticket_probability"],
                "mean_simulated_draws_until_jackpot_hit": safe_mean(
                    [float(row["mean_draws_until_jackpot_hit"]) for row in rows]
                ),
                "mean_simulated_misses_before_jackpot_hit": safe_mean(
                    [float(row["mean_misses_before_jackpot_hit"]) for row in rows]
                ),
                "mean_jackpot_hits_per_run": safe_mean(
                    [float(row["jackpot_hit_count"]) for row in rows]
                ),
                "mean_no_winner_draw_share": safe_mean(
                    [float(row["no_winner_draw_share"]) for row in rows]
                ),
                "mean_time_to_cap": safe_mean(
                    [float(row["time_to_cap"]) for row in rows if row["time_to_cap"] != ""]
                ),
                "cap_reach_rate": safe_mean(
                    [1.0 if row["reached_cap"] == "True" else 0.0 for row in rows]
                ),
                "mean_draws_at_cap": safe_mean(
                    [float(row["draws_at_cap"]) for row in rows]
                ),
                "mean_max_jackpot_fund_observed": safe_mean(
                    [float(row["max_jackpot_fund_observed"]) for row in rows]
                ),
                "mean_average_jackpot_available": safe_mean(
                    [float(row["average_jackpot_available"]) for row in rows]
                ),
                "mean_total_overflow_to_class2": safe_mean(
                    [float(row["total_overflow_to_class2"]) for row in rows]
                ),
            }
        )

    baseline = next((row for row in summary_rows if row["scenario"] == "uniform_market"), None)
    if baseline is None:
        return summary_rows

    baseline_coverage = float(baseline["coverage_ratio"])
    baseline_wait = float(baseline["mean_simulated_draws_until_jackpot_hit"])
    baseline_time_to_cap = float(baseline["mean_time_to_cap"])
    baseline_avg_jackpot = float(baseline["mean_average_jackpot_available"])
    baseline_overflow = float(baseline["mean_total_overflow_to_class2"])

    for row in summary_rows:
        row["coverage_loss_vs_uniform"] = (
            (baseline_coverage - float(row["coverage_ratio"])) / baseline_coverage
            if baseline_coverage > 0
            else 0.0
        )
        row["rollover_wait_multiplier_vs_uniform"] = (
            float(row["mean_simulated_draws_until_jackpot_hit"]) / baseline_wait
            if baseline_wait > 0
            else 0.0
        )
        row["time_to_cap_multiplier_vs_uniform"] = (
            float(row["mean_time_to_cap"]) / baseline_time_to_cap
            if baseline_time_to_cap > 0
            else 0.0
        )
        row["average_jackpot_multiplier_vs_uniform"] = (
            float(row["mean_average_jackpot_available"]) / baseline_avg_jackpot
            if baseline_avg_jackpot > 0
            else 0.0
        )
        row["overflow_multiplier_vs_uniform"] = (
            float(row["mean_total_overflow_to_class2"]) / baseline_overflow
            if baseline_overflow > 0
            else 0.0
        )

    return summary_rows


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_rows: list[dict] = []

    for scenario_index, scenario in enumerate(H1_COVERAGE_SCENARIOS):
        print(f"Running scenario: {scenario.name}")
        for repetition in range(H1_COVERAGE_CONFIG.repetitions):
            seed = H1_COVERAGE_CONFIG.base_seed + scenario_index * 10_000 + repetition
            stats = run_h1_coverage_simulation(
                config=H1_COVERAGE_CONFIG,
                scenario=scenario,
                seed=seed,
            )

            run_rows.append(
                {
                    "experiment": "h1_coverage_gap",
                    "scenario": scenario.name,
                    "label_cs": scenario.label_cs,
                    "description": scenario.description,
                    "repetition": repetition + 1,
                    "seed": seed,
                    "draws_per_run": H1_COVERAGE_CONFIG.draws_per_run,
                    "tickets_sold_per_draw": H1_COVERAGE_CONFIG.tickets_sold_per_draw,
                    "total_jackpot_combinations": TOTAL_JACKPOT_COMBINATIONS,
                    "date_only_jackpot_combinations": DATE_ONLY_JACKPOT_COMBINATIONS,
                    "popular_ticket_bank_size": len(POPULAR_EXACT_TICKET_LABELS),
                    "uniform_share": scenario.uniform_share,
                    "date_only_share": scenario.date_only_share,
                    "popular_share": scenario.popular_share,
                    "expected_unique_coverage": stats.expected_unique_coverage,
                    "coverage_ratio": stats.coverage_ratio,
                    "jackpot_hit_probability": stats.jackpot_hit_probability,
                    "no_jackpot_winner_probability": stats.no_jackpot_winner_probability,
                    "expected_draws_until_jackpot_hit": 1.0 / stats.jackpot_hit_probability,
                    "exact_ticket_hhi": stats.exact_ticket_hhi,
                    "effective_ticket_support": stats.effective_ticket_support,
                    "max_exact_ticket_probability": stats.max_exact_ticket_probability,
                    "mean_draws_until_jackpot_hit": stats.mean_draws_until_jackpot_hit,
                    "mean_misses_before_jackpot_hit": stats.mean_misses_before_jackpot_hit,
                    "jackpot_hit_count": stats.jackpot_hit_count,
                    "no_winner_draw_share": stats.no_winner_draw_share,
                    "time_to_cap": stats.mean_time_to_cap if stats.mean_time_to_cap is not None else "",
                    "reached_cap": stats.reached_cap,
                    "draws_at_cap": stats.draws_at_cap,
                    "max_jackpot_fund_observed": stats.max_jackpot_fund_observed,
                    "average_jackpot_available": stats.average_jackpot_available,
                    "total_overflow_to_class2": stats.total_overflow_to_class2,
                }
            )

    summary_rows = build_summary_rows(run_rows)

    write_csv(run_rows, RESULTS_DIR / f"h1_coverage_gap_runs_{timestamp}.csv")
    write_csv(summary_rows, RESULTS_DIR / f"h1_coverage_gap_summary_{timestamp}.csv")

    print("\nExperiment H1 coverage gap finished.")
    print(f"Saved CSV files to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()