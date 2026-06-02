"""Run rebuilt H1 experiment: non-random choice and parimutuel dilution."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean

from experiments.h1_choice_scenarios import H1_CHOICE_SCENARIOS, H1_EXPERIMENT_CONFIG
from experiments.h1_market_model import run_h1_market_experiment

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


def build_overall_summary_rows(run_rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in run_rows:
        grouped[row["scenario"]].append(row)

    summary_rows: list[dict] = []

    for scenario in H1_CHOICE_SCENARIOS:
        rows = grouped[scenario.name]
        if not rows:
            continue

        summary_rows.append(
            {
                "experiment": "h1_choice_bias",
                "scenario": scenario.name,
                "label_cs": scenario.label_cs,
                "description": scenario.description,
                "draws": rows[0]["draws"],
                "repetitions": len(rows),
                "tickets_sold_per_draw": rows[0]["tickets_sold_per_draw"],
                "uniform_share": rows[0]["uniform_share"],
                "date_only_share": rows[0]["date_only_share"],
                "popular_share": rows[0]["popular_share"],
                "mean_total_actual_payout": safe_mean([float(row["total_actual_payout"]) for row in rows]),
                "mean_total_theoretical_prize_pool": safe_mean(
                    [float(row["total_theoretical_prize_pool"]) for row in rows]
                ),
                "mean_winner_ticket_count": safe_mean([float(row["winner_ticket_count"]) for row in rows]),
                "mean_winner_ticket_share": safe_mean([float(row["winner_ticket_share"]) for row in rows]),
                "mean_individual_payout_winners": safe_mean(
                    [float(row["mean_individual_payout_winners"]) for row in rows]
                ),
                "median_individual_payout_winners": safe_mean(
                    [float(row["median_individual_payout_winners"]) for row in rows]
                ),
                "payout_variance_winners": safe_mean(
                    [float(row["payout_variance_winners"]) for row in rows]
                ),
                "mean_individual_return_winners": safe_mean(
                    [float(row["mean_individual_return_winners"]) for row in rows]
                ),
                "median_individual_return_winners": safe_mean(
                    [float(row["median_individual_return_winners"]) for row in rows]
                ),
                "return_variance_winners": safe_mean(
                    [float(row["return_variance_winners"]) for row in rows]
                ),
                "mean_return_all_tickets": safe_mean(
                    [float(row["mean_return_all_tickets"]) for row in rows]
                ),
                "return_variance_all_tickets": safe_mean(
                    [float(row["return_variance_all_tickets"]) for row in rows]
                ),
                "exact_ticket_hhi": rows[0]["exact_ticket_hhi"],
                "effective_ticket_support": rows[0]["effective_ticket_support"],
                "max_exact_ticket_probability": rows[0]["max_exact_ticket_probability"],
            }
        )

    baseline = next((row for row in summary_rows if row["scenario"] == "uniform_market"), None)
    if baseline is None:
        return summary_rows

    baseline_median_payout = float(baseline["median_individual_payout_winners"])
    baseline_mean_payout = float(baseline["mean_individual_payout_winners"])
    baseline_return_variance_winners = float(baseline["return_variance_winners"])
    baseline_return_variance_all = float(baseline["return_variance_all_tickets"])

    for row in summary_rows:
        row["median_payout_compression_vs_uniform"] = (
            float(row["median_individual_payout_winners"]) / baseline_median_payout
            if baseline_median_payout > 0
            else 0.0
        )
        row["mean_payout_compression_vs_uniform"] = (
            float(row["mean_individual_payout_winners"]) / baseline_mean_payout
            if baseline_mean_payout > 0
            else 0.0
        )
        row["winner_return_variance_multiplier_vs_uniform"] = (
            float(row["return_variance_winners"]) / baseline_return_variance_winners
            if baseline_return_variance_winners > 0
            else 0.0
        )
        row["all_ticket_return_variance_multiplier_vs_uniform"] = (
            float(row["return_variance_all_tickets"]) / baseline_return_variance_all
            if baseline_return_variance_all > 0
            else 0.0
        )

    return summary_rows


def build_class_summary_rows(class_run_rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in class_run_rows:
        grouped[(row["scenario"], row["class_key"])].append(row)

    class_summary_rows: list[dict] = []

    for scenario in H1_CHOICE_SCENARIOS:
        for class_number in range(1, 13):
            class_key = f"Class {class_number}"
            rows = grouped[(scenario.name, class_key)]
            if not rows:
                continue

            class_summary_rows.append(
                {
                    "experiment": "h1_choice_bias",
                    "scenario": scenario.name,
                    "label_cs": scenario.label_cs,
                    "description": scenario.description,
                    "class_key": class_key,
                    "class_number": class_number,
                    "repetitions": len(rows),
                    "mean_hit_draws": safe_mean([float(row["hit_draws"]) for row in rows]),
                    "mean_total_winners": safe_mean([float(row["total_winners"]) for row in rows]),
                    "mean_winners_per_draw": safe_mean([float(row["mean_winners_per_draw"]) for row in rows]),
                    "mean_winners_when_hit": safe_mean([float(row["mean_winners_when_hit"]) for row in rows]),
                    "mean_individual_payout": safe_mean([float(row["mean_individual_payout"]) for row in rows]),
                    "median_individual_payout": safe_mean([float(row["median_individual_payout"]) for row in rows]),
                    "payout_variance": safe_mean([float(row["payout_variance"]) for row in rows]),
                    "mean_individual_return": safe_mean([float(row["mean_individual_return"]) for row in rows]),
                    "median_individual_return": safe_mean([float(row["median_individual_return"]) for row in rows]),
                    "return_variance": safe_mean([float(row["return_variance"]) for row in rows]),
                }
            )

    baseline_by_class = {
        row["class_key"]: row for row in class_summary_rows if row["scenario"] == "uniform_market"
    }

    for row in class_summary_rows:
        baseline = baseline_by_class.get(row["class_key"])
        if baseline is None:
            continue

        baseline_median_payout = float(baseline["median_individual_payout"])
        baseline_mean_payout = float(baseline["mean_individual_payout"])
        baseline_mean_winners = float(baseline["mean_winners_when_hit"])

        row["median_payout_compression_vs_uniform"] = (
            float(row["median_individual_payout"]) / baseline_median_payout
            if baseline_median_payout > 0
            else 0.0
        )
        row["mean_payout_compression_vs_uniform"] = (
            float(row["mean_individual_payout"]) / baseline_mean_payout
            if baseline_mean_payout > 0
            else 0.0
        )
        row["winner_multiplier_vs_uniform"] = (
            float(row["mean_winners_when_hit"]) / baseline_mean_winners
            if baseline_mean_winners > 0
            else 0.0
        )

    class_summary_rows.sort(key=lambda row: (row["class_number"], row["scenario"]))
    return class_summary_rows


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_rows: list[dict] = []
    class_run_rows: list[dict] = []

    for scenario_index, scenario in enumerate(H1_CHOICE_SCENARIOS):
        for repetition in range(H1_EXPERIMENT_CONFIG.repetitions):
            seed = H1_EXPERIMENT_CONFIG.base_seed + scenario_index * 10_000 + repetition

            stats = run_h1_market_experiment(
                config=H1_EXPERIMENT_CONFIG,
                scenario=scenario,
                seed=seed,
            )

            run_rows.append(
                {
                    "experiment": "h1_choice_bias",
                    "scenario": scenario.name,
                    "label_cs": scenario.label_cs,
                    "description": scenario.description,
                    "repetition": repetition + 1,
                    "seed": seed,
                    "draws": stats.draws_simulated,
                    "tickets_sold_per_draw": stats.tickets_sold_per_draw,
                    "uniform_share": scenario.uniform_share,
                    "date_only_share": scenario.date_only_share,
                    "popular_share": scenario.popular_share,
                    "total_ticket_sales": stats.total_ticket_sales,
                    "total_theoretical_prize_pool": stats.total_theoretical_prize_pool,
                    "total_actual_payout": stats.total_actual_payout,
                    "winner_ticket_count": stats.winner_ticket_count,
                    "winner_ticket_share": stats.winner_ticket_share,
                    "mean_individual_payout_winners": stats.mean_individual_payout_winners,
                    "median_individual_payout_winners": stats.median_individual_payout_winners,
                    "payout_variance_winners": stats.payout_variance_winners,
                    "mean_individual_return_winners": stats.mean_individual_return_winners,
                    "median_individual_return_winners": stats.median_individual_return_winners,
                    "return_variance_winners": stats.return_variance_winners,
                    "mean_return_all_tickets": stats.mean_return_all_tickets,
                    "return_variance_all_tickets": stats.return_variance_all_tickets,
                    "exact_ticket_hhi": stats.exact_ticket_hhi,
                    "effective_ticket_support": stats.effective_ticket_support,
                    "max_exact_ticket_probability": stats.max_exact_ticket_probability,
                }
            )

            for class_key, class_stats in stats.class_stats.items():
                class_run_rows.append(
                    {
                        "experiment": "h1_choice_bias",
                        "scenario": scenario.name,
                        "label_cs": scenario.label_cs,
                        "description": scenario.description,
                        "repetition": repetition + 1,
                        "seed": seed,
                        "draws": stats.draws_simulated,
                        "class_key": class_key,
                        "class_number": class_stats.class_number,
                        "hit_draws": class_stats.hit_draws,
                        "total_winners": class_stats.total_winners,
                        "mean_winners_per_draw": class_stats.mean_winners_per_draw,
                        "mean_winners_when_hit": class_stats.mean_winners_when_hit,
                        "mean_individual_payout": class_stats.mean_individual_payout,
                        "median_individual_payout": class_stats.median_individual_payout,
                        "payout_variance": class_stats.payout_variance,
                        "mean_individual_return": class_stats.mean_individual_return,
                        "median_individual_return": class_stats.median_individual_return,
                        "return_variance": class_stats.return_variance,
                    }
                )

    overall_summary_rows = build_overall_summary_rows(run_rows)
    class_summary_rows = build_class_summary_rows(class_run_rows)

    write_csv(run_rows, RESULTS_DIR / f"h1_choice_bias_runs_{timestamp}.csv")
    write_csv(class_run_rows, RESULTS_DIR / f"h1_choice_bias_class_runs_{timestamp}.csv")
    write_csv(overall_summary_rows, RESULTS_DIR / f"h1_choice_bias_summary_{timestamp}.csv")
    write_csv(class_summary_rows, RESULTS_DIR / f"h1_choice_bias_class_summary_{timestamp}.csv")

    print("\nRebuilt H1 experiment finished.")
    print(f"Saved CSV files to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()