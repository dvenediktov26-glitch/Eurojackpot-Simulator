"""Create Czech-language plots for chapter 3.

Run from the backend directory:
    python -m experiments.make_plots
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb
import numpy as np


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = BASE_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

FACULTY_COLOR = "#00957d"


def find_latest(pattern: str) -> Path:
    """Return latest file matching the pattern."""
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")
    return matches[-1]


def load_csv_rows(path: Path) -> list[dict]:
    """Load rows from a CSV file."""
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def format_int_cs(value: int | float) -> str:
    """Format integer using Czech thousands separator."""
    return f"{int(round(value)):,}".replace(",", " ")


def lighten_color(hex_color: str, factor: float) -> tuple[float, float, float]:
    """Return lighter variant of a color."""
    r, g, b = to_rgb(hex_color)
    return (
        r + (1 - r) * factor,
        g + (1 - g) * factor,
        b + (1 - b) * factor,
    )


def probability_label(probability: float) -> str:
    """Format probabilities for heatmap labels.

    Rules:
    - 0 -> "0"
    - >= 0.001 -> show as percent
    - smaller positive values -> scientific notation
    """
    if probability <= 0:
        return "0"

    if probability >= 0.001:
        return f"{probability * 100:.1f} %"

    exponent = int(math.floor(math.log10(probability)))
    mantissa = probability / (10**exponent)
    return f"{mantissa:.1f}×10^{exponent}"


def save_figure(fig: plt.Figure, filename: str) -> None:
    """Save and close a figure."""
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_experiment1_heatmap_from_runs(run_rows: list[dict]) -> None:
    """Heatmap of probabilities of reaching net-result thresholds.

    Uses run-level data directly so we can easily redefine threshold levels.
    """
    thresholds = [0, 100, 10_000, 100_000, 1_000_000, 10_000_000, 100_000_000]
    draws_sorted = sorted({int(row["draws"]) for row in run_rows})

    matrix: list[list[float]] = []
    for threshold in thresholds:
        row_values: list[float] = []
        for draws in draws_sorted:
            scenario_rows = [
                float(row["net_result"])
                for row in run_rows
                if int(row["draws"]) == draws
            ]
            probability = (
                sum(1 for value in scenario_rows if value >= threshold) / len(scenario_rows)
                if scenario_rows
                else 0.0
            )
            row_values.append(probability)
        matrix.append(row_values)

    cmap = LinearSegmentedColormap.from_list(
        "faculty_green",
        ["#ffffff", lighten_color(FACULTY_COLOR, 0.55), FACULTY_COLOR],
    )

    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    image = ax.imshow(matrix, cmap=cmap, aspect="auto")

    ax.set_title("Pravděpodobnost dosažení čistého zisku", fontsize=16, fontweight="bold")
    ax.set_xlabel("Počet odehraných tiketů")
    ax.set_ylabel("Prahová hodnota čistého zisku (€)")
    ax.set_xticks(range(len(draws_sorted)))
    ax.set_xticklabels([format_int_cs(value) for value in draws_sorted])
    ax.set_yticks(range(len(thresholds)))
    ax.set_yticklabels([format_int_cs(value) for value in thresholds])

    for i in range(len(thresholds)):
        for j in range(len(draws_sorted)):
            value = matrix[i][j]
            ax.text(
                j,
                i,
                probability_label(value),
                ha="center",
                va="center",
                fontsize=10,
            )

    fig.colorbar(image, ax=ax, label="Pravděpodobnost")
    save_figure(fig, "experiment1_profit_heatmap.png")


def plot_experiment2_cdf(run_rows: list[dict]) -> None:
    """CDF of tickets until the first jackpot."""
    values = sorted(float(row["tickets_until_jackpot"]) for row in run_rows)
    n = len(values)
    y_values = [(index + 1) / n for index in range(n)]

    median_value = values[n // 2]
    mean_value = sum(values) / n

    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    ax.plot(values, y_values, color=FACULTY_COLOR, linewidth=2.5)
    ax.axvline(
        mean_value,
        color=lighten_color(FACULTY_COLOR, 0.25),
        linestyle="--",
        linewidth=2,
    )
    ax.axvline(median_value, color="black", linestyle=":", linewidth=2)

    ax.set_xscale("log")
    ax.set_title(
        "Kumulativní rozdělení počtu tiketů do prvního jackpotu",
        fontsize=15,
        fontweight="bold",
    )
    ax.set_xlabel("Počet odehraných tiketů")
    ax.set_ylabel("Kumulativní pravděpodobnost")
    ax.grid(True, alpha=0.25)

    ax.text(mean_value, 0.15, "Průměr", rotation=90, va="bottom", ha="right", fontsize=10)
    ax.text(median_value, 0.15, "Medián", rotation=90, va="bottom", ha="left", fontsize=10)

    save_figure(fig, "experiment2_jackpot_cdf.png")


def plot_experiment2_scatter(run_rows: list[dict]) -> None:
    """Scatter plot of tickets until jackpot vs approximate net result."""
    x_values = [float(row["tickets_until_jackpot"]) for row in run_rows]
    y_values_millions = [float(row["approx_net_result_eur"]) / 1_000_000 for row in run_rows]

    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    ax.scatter(
        x_values,
        y_values_millions,
        color=FACULTY_COLOR,
        alpha=0.22,
        s=18,
        edgecolors="none",
    )
    ax.axhline(0, color="black", linewidth=1, alpha=0.7)
    ax.set_xscale("log")
    ax.set_title("Čistý výsledek při prvním jackpotu", fontsize=15, fontweight="bold")
    ax.set_xlabel("Počet odehraných tiketů")
    ax.set_ylabel("Čistý výsledek (mil. €)")
    ax.grid(True, alpha=0.25)

    save_figure(fig, "experiment2_jackpot_net_result_scatter.png")


def plot_experiment3_median_rtp_bars(run_rows: list[dict]) -> None:
    """Grouped bar chart of median RTP by market size and model."""
    data: dict[tuple[int, str], list[float]] = {}

    for row in run_rows:
        market_size = int(row["tickets_sold_per_draw"])
        model = str(row["market_model"])
        rtp = float(row["rtp"])
        data.setdefault((market_size, model), []).append(rtp)

    market_sizes = sorted({key[0] for key in data.keys()})

    uniform_values = []
    realistic_values = []

    for market_size in market_sizes:
        uniform_rtps = sorted(data[(market_size, "uniform")])
        realistic_rtps = sorted(data[(market_size, "realistic")])

        uniform_median = float(np.median(uniform_rtps))
        realistic_median = float(np.median(realistic_rtps))

        uniform_values.append(uniform_median)
        realistic_values.append(realistic_median)

    x = np.arange(len(market_sizes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10.8, 6.2))
    bars_uniform = ax.bar(
        x - width / 2,
        uniform_values,
        width,
        label="Rovnoměrný model",
        color=lighten_color(FACULTY_COLOR, 0.35),
    )
    bars_realistic = ax.bar(
        x + width / 2,
        realistic_values,
        width,
        label="Realistický model",
        color=FACULTY_COLOR,
    )

    ax.set_title("Medián RTP podle velikosti trhu", fontsize=16, fontweight="bold")
    ax.set_xlabel("Počet prodaných tiketů na losování")
    ax.set_ylabel("Medián RTP")
    ax.set_xticks(x)
    ax.set_xticklabels([format_int_cs(value) for value in market_sizes])
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)

    for bars in (bars_uniform, bars_realistic):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                f"{value:.4f}".replace(".", ","),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=9,
            )

    save_figure(fig, "experiment3_median_rtp_bars.png")


def plot_experiment3_median_rtp_bars(run_rows: list[dict]) -> None:
    """Grouped bar chart of median RTP by market size and model."""
    data: dict[tuple[int, str], list[float]] = {}

    for row in run_rows:
        market_size = int(row["tickets_sold_per_draw"])
        model = str(row["market_model"])
        rtp = float(row["rtp"])
        data.setdefault((market_size, model), []).append(rtp)

    market_sizes = sorted({key[0] for key in data.keys()})

    uniform_values = []
    realistic_values = []

    for market_size in market_sizes:
        uniform_rtps = sorted(data[(market_size, "uniform")])
        realistic_rtps = sorted(data[(market_size, "realistic")])

        uniform_median = float(np.median(uniform_rtps))
        realistic_median = float(np.median(realistic_rtps))

        uniform_values.append(uniform_median)
        realistic_values.append(realistic_median)

    x = np.arange(len(market_sizes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    bars_uniform = ax.bar(
        x - width / 2,
        uniform_values,
        width,
        label="Rovnoměrný model",
        color=lighten_color(FACULTY_COLOR, 0.35),
    )
    bars_realistic = ax.bar(
        x + width / 2,
        realistic_values,
        width,
        label="Realistický model",
        color=FACULTY_COLOR,
    )

    ax.set_title("Medián RTP podle velikosti trhu", fontsize=16, fontweight="bold")
    ax.set_xlabel("Počet prodaných tiketů na losování")
    ax.set_ylabel("Medián RTP")
    ax.set_xticks(x)
    ax.set_xticklabels([format_int_cs(value) for value in market_sizes])

    # Поднимаем верхнюю границу оси Y, чтобы подписи не упирались в верх графика.
    ax.set_ylim(0, 0.25)

    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)

    for bars in (bars_uniform, bars_realistic):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                f"{value:.4f}".replace(".", ","),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 8),
                ha="center",
                fontsize=9,
            )

    save_figure(fig, "experiment3_median_rtp_bars.png")


def main() -> None:
    """Generate plots from the newest experiment outputs."""
    experiment1_runs = load_csv_rows(find_latest("experiment1_profit_runs_*.csv"))
    experiment2_runs = load_csv_rows(find_latest("experiment2_jackpot_runs_*.csv"))
    experiment3_runs = load_csv_rows(find_latest("experiment3_rtp_market_runs_*.csv"))

    plot_experiment1_heatmap_from_runs(experiment1_runs)
    plot_experiment2_cdf(experiment2_runs)
    plot_experiment2_scatter(experiment2_runs)
    plot_experiment3_median_rtp_bars(experiment3_runs)

    print(f"Plots saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()