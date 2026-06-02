"""Build plots for H1: coverage gap and rollover acceleration.

Run from the backend directory:
    python -m experiments.make_h1_coverage_plots
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

FACULTY_COLOR = "#00957d"


def lighten_color(hex_color: str, factor: float) -> tuple[float, float, float]:
    """Return a lighter RGB tuple derived from one hex color."""
    hex_color = hex_color.lstrip("#")
    red = int(hex_color[0:2], 16) / 255.0
    green = int(hex_color[2:4], 16) / 255.0
    blue = int(hex_color[4:6], 16) / 255.0
    return (
        red + (1.0 - red) * factor,
        green + (1.0 - green) * factor,
        blue + (1.0 - blue) * factor,
    )


def format_int_cs(value: int | float) -> str:
    return f"{int(round(value)):,}".replace(",", " ")


def format_float_cs(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def format_percent_cs(value: float, decimals: int = 2) -> str:
    return f"{value * 100:.{decimals}f} %".replace(".", ",")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def find_latest(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No result file found for pattern: {pattern}")
    return matches[-1]


def sort_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    order = {
        "uniform_market": 0,
        "mildly_clustered_market": 1,
        "strongly_clustered_market": 2,
    }
    return sorted(rows, key=lambda row: order.get(row["scenario"], 999))


def save_figure(fig: plt.Figure, filename: str) -> None:
    output_path = FIGURES_DIR / filename
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure: {output_path}")


def plot_h1_coverage_gap(rows: list[dict[str, str]]) -> None:
    labels = [row["label_cs"] for row in rows]
    unique_coverage_millions = [float(row["expected_unique_coverage"]) / 1_000_000 for row in rows]
    coverage_ratio_percent = [float(row["coverage_ratio"]) * 100 for row in rows]

    x = np.arange(len(labels))

    fig, ax1 = plt.subplots(figsize=(11.0, 6.6))
    bars = ax1.bar(labels, unique_coverage_millions, color=FACULTY_COLOR, width=0.55)
    ax1.set_title("Pokrytí jackpotového prostoru podle profilu trhu", fontsize=16, fontweight="bold")
    ax1.set_xlabel("Profil trhu")
    ax1.set_ylabel("Unikátně pokryté kombinace (mil.)")
    ax1.grid(True, axis="y", alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(x, coverage_ratio_percent, marker="o", linewidth=2.2, markersize=7)
    ax2.set_ylabel("Pokrytí prostoru (%)")
    ax2.set_ylim(0, max(coverage_ratio_percent) * 1.25)

    for bar, ratio in zip(bars, coverage_ratio_percent):
        value = bar.get_height()
        ax1.annotate(
            format_float_cs(value, 2),
            (bar.get_x() + bar.get_width() / 2, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=9,
        )
        ax2.annotate(
            format_float_cs(ratio, 2) + " %",
            (bar.get_x() + bar.get_width() / 2, ratio),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
        )

    save_figure(fig, "h1_coverage_gap.png")


def plot_h1_no_winner_probability(rows: list[dict[str, str]]) -> None:
    labels = [row["label_cs"] for row in rows]
    jackpot_hit_probability = [float(row["jackpot_hit_probability"]) for row in rows]
    no_winner_probability = [float(row["no_jackpot_winner_probability"]) for row in rows]

    x = np.arange(len(labels))
    width = 0.34

    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    bars_hit = ax.bar(
        x - width / 2,
        jackpot_hit_probability,
        width,
        label="Pravděpodobnost jackpot hit",
        color=FACULTY_COLOR,
    )
    bars_miss = ax.bar(
        x + width / 2,
        no_winner_probability,
        width,
        label="Pravděpodobnost losování bez vítěze",
        color=lighten_color(FACULTY_COLOR, 0.40),
    )

    ax.set_title("Pravděpodobnost jackpot hit a losování bez vítěze", fontsize=16, fontweight="bold")
    ax.set_xlabel("Profil trhu")
    ax.set_ylabel("Pravděpodobnost")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=True)
    ax.grid(True, axis="y", alpha=0.25)
    fig.subplots_adjust(bottom=0.20)

    for bars in (bars_hit, bars_miss):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                format_percent_cs(value, 2),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    save_figure(fig, "h1_no_winner_probability.png")


def plot_h1_rollover_wait(rows: list[dict[str, str]]) -> None:
    labels = [row["label_cs"] for row in rows]
    analytical_wait = [float(row["expected_draws_until_jackpot_hit"]) for row in rows]
    simulated_wait = [float(row["mean_simulated_draws_until_jackpot_hit"]) for row in rows]

    x = np.arange(len(labels))
    width = 0.34

    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    bars_analytical = ax.bar(
        x - width / 2,
        analytical_wait,
        width,
        label="Analytický odhad",
        color=FACULTY_COLOR,
    )
    bars_simulated = ax.bar(
        x + width / 2,
        simulated_wait,
        width,
        label="Simulovaný průměr",
        color=lighten_color(FACULTY_COLOR, 0.40),
    )

    ax.set_title("Průměrný počet losování do zásahu jackpotu", fontsize=16, fontweight="bold")
    ax.set_xlabel("Profil trhu")
    ax.set_ylabel("Počet losování")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)

    for bars in (bars_analytical, bars_simulated):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                format_float_cs(value, 2),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=9,
            )

    save_figure(fig, "h1_rollover_wait.png")


def plot_h1_cap_pressure(rows: list[dict[str, str]]) -> None:
    labels = [row["label_cs"] for row in rows]
    time_to_cap = [float(row["mean_time_to_cap"]) for row in rows]
    average_jackpot_millions = [float(row["mean_average_jackpot_available"]) / 1_000_000 for row in rows]

    x = np.arange(len(labels))
    width = 0.34

    fig, ax1 = plt.subplots(figsize=(11.0, 6.6))
    bars = ax1.bar(
        x - width / 2,
        time_to_cap,
        width,
        label="Průměrný čas do dosažení stropu",
        color=FACULTY_COLOR,
    )
    ax1.set_title("Tlak na jackpot cap podle profilu trhu", fontsize=16, fontweight="bold")
    ax1.set_xlabel("Profil trhu")
    ax1.set_ylabel("Počet losování")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.grid(True, axis="y", alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(
        x + width / 2,
        average_jackpot_millions,
        marker="o",
        linewidth=2.2,
        markersize=7,
        label="Průměrný dostupný jackpot",
        color=lighten_color(FACULTY_COLOR, 0.15),
    )
    ax2.set_ylabel("Průměrný dostupný jackpot (mil. EUR)")

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=True)
    fig.subplots_adjust(bottom=0.20)

    for bar in bars:
        value = bar.get_height()
        ax1.annotate(
            format_float_cs(value, 1),
            (bar.get_x() + bar.get_width() / 2, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=9,
        )

    for xpos, value in zip(x + width / 2, average_jackpot_millions):
        ax2.annotate(
            format_float_cs(value, 1),
            (xpos, value),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
        )

    save_figure(fig, "h1_cap_pressure.png")


def main() -> None:
    rows = sort_rows(load_csv_rows(find_latest("h1_coverage_gap_summary_*.csv")))

    plot_h1_coverage_gap(rows)
    plot_h1_no_winner_probability(rows)
    plot_h1_rollover_wait(rows)
    plot_h1_cap_pressure(rows)

    print(f"Plots saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()