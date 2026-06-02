"""Build figures for the redesigned operator-focused chapter 3 experiments."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

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


def format_int_cs(value: int) -> str:
    """Format an integer with Czech thousands separators."""
    return f"{value:,}".replace(",", " ")


def format_float_cs(value: float, decimals: int = 2) -> str:
    """Format a float with Czech decimal separator."""
    return f"{value:.{decimals}f}".replace(".", ",")


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def find_latest(pattern: str) -> Path:
    """Find the newest CSV result matching a pattern."""
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No result file found for pattern: {pattern}")
    return matches[-1]


def save_figure(fig: plt.Figure, filename: str) -> None:
    """Save one matplotlib figure and close it."""
    output_path = FIGURES_DIR / filename
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure: {output_path}")


def open_figures_dir() -> None:
    """Open the figures directory in the system file manager."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(FIGURES_DIR)], check=False)
        elif sys.platform.startswith("win"):
            subprocess.run(["explorer", str(FIGURES_DIR)], check=False)
        else:
            subprocess.run(["xdg-open", str(FIGURES_DIR)], check=False)
    except Exception as exc:
        print(f"Could not open figures directory automatically: {exc}")


def sort_h3_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return H3 rows in the logical order: lower -> standard -> higher skewness."""
    order = {
        "Nižší skewness": 0,
        "Standardní": 1,
        "Vyšší skewness": 2,
    }
    return sorted(rows, key=lambda row: order.get(row["label_cs"], 999))


def plot_h2_rollover_and_cap(rows: list[dict[str, str]]) -> None:
    """Grouped bars for rollover length and time-to-cap by jackpot cap."""
    labels = [row["label_cs"] for row in rows]
    rollover_values = [float(row["mean_average_rollover_length"]) for row in rows]
    time_to_cap_values = [float(row["mean_average_time_to_cap"]) for row in rows]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    bars_rollover = ax.bar(
        x - width / 2,
        rollover_values,
        width,
        label="Průměrná délka rollover série",
        color=FACULTY_COLOR,
    )
    bars_time_to_cap = ax.bar(
        x + width / 2,
        time_to_cap_values,
        width,
        label="Průměrný čas do dosažení stropu",
        color=lighten_color(FACULTY_COLOR, 0.40),
    )

    ax.set_title("Vliv stropu jackpotu na rollover dynamiku", fontsize=16, fontweight="bold")
    ax.set_xlabel("Strop jackpotu")
    ax.set_ylabel("Počet losování")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)

    for bars in (bars_rollover, bars_time_to_cap):
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

    save_figure(fig, "h2_rollover_and_time_to_cap.png")


def plot_h2_payout_volatility(rows: list[dict[str, str]]) -> None:
    """Bar chart for payout volatility by jackpot cap."""
    labels = [row["label_cs"] for row in rows]
    payout_std_values = [float(row["mean_payout_std_dev"]) for row in rows]
    upper_tier_std_values = [float(row["mean_upper_tier_payout_std_dev"]) for row in rows]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    bars_total = ax.bar(
        x - width / 2,
        payout_std_values,
        width,
        label="Směrodatná odchylka celkových výplat",
        color=FACULTY_COLOR,
    )
    bars_upper = ax.bar(
        x + width / 2,
        upper_tier_std_values,
        width,
        label="Směrodatná odchylka horních tříd",
        color=lighten_color(FACULTY_COLOR, 0.40),
    )

    ax.set_title("Volatilita výplat podle stropu jackpotu", fontsize=16, fontweight="bold")
    ax.set_xlabel("Strop jackpotu")
    ax.set_ylabel("EUR")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)

    for bars in (bars_total, bars_upper):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                format_int_cs(int(round(value))),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    save_figure(fig, "h2_payout_volatility.png")


def plot_h2_overflow(rows: list[dict[str, str]]) -> None:
    """Grouped bars for overflow redirected to Classes 2 and 3."""
    labels = [row["label_cs"] for row in rows]
    overflow_class2 = [float(row["mean_overflow_to_class2"]) for row in rows]
    overflow_class3 = [float(row["mean_overflow_to_class3"]) for row in rows]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    bars_c2 = ax.bar(
        x - width / 2,
        overflow_class2,
        width,
        label="Overflow do třídy 2",
        color=FACULTY_COLOR,
    )
    bars_c3 = ax.bar(
        x + width / 2,
        overflow_class3,
        width,
        label="Overflow do třídy 3",
        color=lighten_color(FACULTY_COLOR, 0.40),
    )

    ax.set_title("Přelití prostředků při různých stropech jackpotu", fontsize=16, fontweight="bold")
    ax.set_xlabel("Strop jackpotu")
    ax.set_ylabel("EUR za běh")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)

    for bars in (bars_c2, bars_c3):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                format_int_cs(int(round(value))),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    save_figure(fig, "h2_overflow.png")


def plot_h3_jackpot_dynamics(rows: list[dict[str, str]]) -> None:
    """
    Show average available jackpot and average overflow to Class 2
    by prize-structure scenario.
    """
    rows = sort_h3_rows(rows)

    labels = [row["label_cs"] for row in rows]
    avg_jackpot_values = [float(row["mean_average_jackpot_available"]) / 1_000_000 for row in rows]
    avg_overflow_class2_values = [
    float(row["mean_overflow_to_class2"]) / float(row["draws"]) / 1_000_000
    for row in rows
    ]

    x = np.arange(len(labels))
    line_x = x + 0.08

    fig, ax1 = plt.subplots(figsize=(11.4, 6.8))
    ax2 = ax1.twinx()

    bars = ax1.bar(
        x,
        avg_jackpot_values,
        width=0.52,
        label="Průměrně dostupný jackpot",
        color=FACULTY_COLOR,
        zorder=3,
    )

    (line,) = ax2.plot(
        line_x,
        avg_overflow_class2_values,
        marker="o",
        linewidth=2.4,
        markersize=8,
        label="Průměrný overflow do třídy 2",
        color=lighten_color(FACULTY_COLOR, 0.35),
        zorder=4,
    )

    ax1.set_title("Vliv šikmosti rozdělení fondu na jackpot a overflow", fontsize=16, fontweight="bold")
    ax1.set_xlabel("Profil rozdělení fondu")
    ax1.set_ylabel("Průměrně dostupný jackpot (mil. EUR)")
    ax2.set_ylabel("Průměrný overflow do třídy 2 na losování (mil. EUR)")

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.grid(True, axis="y", alpha=0.22)

    max_bar = max(avg_jackpot_values) if avg_jackpot_values else 1.0
    max_line = max(avg_overflow_class2_values) if avg_overflow_class2_values else 1.0
    ax1.set_ylim(0, max_bar * 1.18)
    ax2.set_ylim(0, max_line * 1.18)

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        handles1 + [line],
        labels1 + labels2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=2,
        frameon=True,
        fontsize=10,
    )

    for bar in bars:
        value = bar.get_height()
        ax1.annotate(
            format_float_cs(value, 2),
            (bar.get_x() + bar.get_width() / 2, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=9,
        )

    for xi, value in zip(line_x, avg_overflow_class2_values):
        ax2.annotate(
            format_float_cs(value, 1),
            (xi, value),
            textcoords="offset points",
            xytext=(8, 10),
            ha="left",
            fontsize=9,
        )

    save_figure(fig, "h3_jackpot_dynamics.png")


def plot_h3_time_to_cap(rows: list[dict[str, str]]) -> None:
    """Bar chart for average time to cap under different prize structures."""
    rows = sort_h3_rows(rows)

    labels = [row["label_cs"] for row in rows]
    values = [float(row["mean_average_time_to_cap"]) for row in rows]

    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    bars = ax.bar(labels, values, color=FACULTY_COLOR)

    ax.set_title("Čas do dosažení stropu podle struktury fondu", fontsize=16, fontweight="bold")
    ax.set_xlabel("Profil rozdělení fondu")
    ax.set_ylabel("Počet losování")
    ax.grid(True, axis="y", alpha=0.25)

    max_value = max(values) if values else 1.0
    ax.set_ylim(0, max_value * 1.15)

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

    save_figure(fig, "h3_time_to_cap.png")


def main() -> None:
    """Build all redesigned chapter 3 figures."""
    h2_rows = load_csv_rows(find_latest("h2_jackpot_cap_summary_*.csv"))
    h3_rows = load_csv_rows(find_latest("h3_prize_structure_summary_*.csv"))

    plot_h2_rollover_and_cap(h2_rows)
    plot_h2_payout_volatility(h2_rows)
    plot_h2_overflow(h2_rows)
    plot_h3_jackpot_dynamics(h3_rows)
    plot_h3_time_to_cap(h3_rows)

    print(f"Plots saved to: {FIGURES_DIR}")
    open_figures_dir()


if __name__ == "__main__":
    main()