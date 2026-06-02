"""Build cleaner plots for rebuilt H1: non-random choice and parimutuel dilution."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

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


COLOR_UNIFORM = FACULTY_COLOR
COLOR_MILD = lighten_color(FACULTY_COLOR, 0.28)
COLOR_STRONG = lighten_color(FACULTY_COLOR, 0.55)

SCENARIO_ORDER = {
    "uniform_market": 0,
    "mild_bias_market": 1,
    "strong_bias_market": 2,
}


def scenario_order_key(scenario: str) -> int:
    return SCENARIO_ORDER.get(scenario, 999)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def find_latest(pattern: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No result file found for pattern: {pattern}")
    return matches[-1]


def save_figure(fig: plt.Figure, filename: str) -> None:
    output_path = FIGURES_DIR / filename
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved figure: {output_path}")


def format_int_cs(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def format_float_cs(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def percent_formatter(x: float, _pos: int) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def sort_summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: scenario_order_key(row["scenario"]))


def sort_class_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: (int(row["class_number"]), scenario_order_key(row["scenario"])),
    )


def build_class_matrix(
    class_rows: list[dict[str, str]],
    field_name: str,
) -> tuple[list[str], dict[str, str], dict[str, list[float]]]:
    scenario_labels: dict[str, str] = {}
    class_numbers = sorted({int(row["class_number"]) for row in class_rows})

    values_by_scenario: dict[str, dict[int, float]] = {}
    for row in class_rows:
        scenario = row["scenario"]
        scenario_labels[scenario] = row["label_cs"]
        values_by_scenario.setdefault(scenario, {})
        values_by_scenario[scenario][int(row["class_number"])] = float(row[field_name])

    ordered_scenarios = sorted(values_by_scenario.keys(), key=scenario_order_key)
    class_labels = [f"T{class_number}" for class_number in class_numbers]

    matrix: dict[str, list[float]] = {}
    for scenario in ordered_scenarios:
        matrix[scenario] = [
            values_by_scenario[scenario].get(class_number, 0.0) for class_number in class_numbers
        ]

    return class_labels, scenario_labels, matrix


def get_scenario_style(scenario: str) -> tuple[str, str]:
    if scenario == "uniform_market":
        return COLOR_UNIFORM, "o"
    if scenario == "mild_bias_market":
        return COLOR_MILD, "s"
    return COLOR_STRONG, "^"


def plot_h1_overall_winner_payouts(summary_rows: list[dict[str, str]]) -> None:
    labels = [row["label_cs"] for row in summary_rows]
    median_values = [float(row["median_individual_payout_winners"]) for row in summary_rows]
    mean_values = [float(row["mean_individual_payout_winners"]) for row in summary_rows]

    x = np.arange(len(labels))
    width = 0.34

    fig, ax = plt.subplots(figsize=(10.8, 6.2))
    bars_median = ax.bar(
        x - width / 2,
        median_values,
        width,
        label="Medián individuální výplaty",
        color=FACULTY_COLOR,
    )
    bars_mean = ax.bar(
        x + width / 2,
        mean_values,
        width,
        label="Průměr individuální výplaty",
        color=lighten_color(FACULTY_COLOR, 0.35),
    )

    ax.set_title("Celková individuální výplata mezi vítěznými tikety", fontsize=16, fontweight="bold")
    ax.set_xlabel("Profil trhu")
    ax.set_ylabel("EUR")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    ncol=2,
    frameon=True,
    fontsize=11,
    )

    fig.subplots_adjust(bottom=0.22)
    ax.grid(True, axis="y", alpha=0.25)

    for bars in (bars_median, bars_mean):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                format_int_cs(int(round(value))),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 5),
                ha="center",
                fontsize=8,
            )

    save_figure(fig, "h1_overall_winner_payouts.png")


def plot_h1_return_variance(summary_rows: list[dict[str, str]]) -> None:
    """Rozptyl návratnosti podle profilu trhu."""
    labels = [row["label_cs"] for row in summary_rows]
    winner_values = [float(row["return_variance_winners"]) for row in summary_rows]
    all_ticket_values = [float(row["return_variance_all_tickets"]) for row in summary_rows]

    x = np.arange(len(labels))
    width = 0.34

    fig, ax = plt.subplots(figsize=(11.5, 7.2))

    bars_winners = ax.bar(
        x - width / 2,
        winner_values,
        width,
        label="Rozptyl mezi vítěznými tikety",
        color=FACULTY_COLOR,
    )
    bars_all = ax.bar(
        x + width / 2,
        all_ticket_values,
        width,
        label="Rozptyl mezi všemi tikety",
        color=lighten_color(FACULTY_COLOR, 0.35),
    )

    ax.set_title("Rozptyl návratnosti podle profilu trhu", fontsize=18, fontweight="bold")
    ax.set_xlabel("Profil trhu", fontsize=13)
    ax.set_ylabel("Rozptyl návratnosti", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_yscale("log")
    ax.grid(True, axis="y", alpha=0.25)

    # Подписи над столбцами: без знаков после запятой
    for bars in (bars_winners, bars_all):
        for bar in bars:
            value = bar.get_height()
            ax.annotate(
                format_int_cs(int(round(value))),
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 5),
                ha="center",
                fontsize=10,
            )

    # Легенда под графиком по центру
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=2,
        frameon=True,
        fontsize=11,
    )

    # Добавляем место снизу для легенды
    fig.subplots_adjust(bottom=0.20)

    save_figure(fig, "h1_return_variance.png")


def plot_h1_class_median_payouts(class_rows: list[dict[str, str]]) -> None:
    class_labels, scenario_labels, matrix = build_class_matrix(class_rows, "median_individual_payout")
    scenarios = sorted(matrix.keys(), key=scenario_order_key)
    x = np.arange(len(class_labels))

    fig, ax = plt.subplots(figsize=(13.8, 6.8))

    for scenario in scenarios:
        color, marker = get_scenario_style(scenario)
        ax.plot(
            x,
            matrix[scenario],
            marker=marker,
            linewidth=2.2,
            markersize=6,
            label=scenario_labels[scenario],
            color=color,
        )

    ax.set_title("Medián individuální výplaty podle výherní třídy", fontsize=16, fontweight="bold")
    ax.set_xlabel("Výherní třída")
    ax.set_ylabel("EUR (log měřítko)")
    ax.set_xticks(x)
    ax.set_xticklabels(class_labels)
    ax.set_yscale("log")
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.25)

    # Подпишем только uniform scenario, чтобы не было каши.
    uniform_values = matrix.get("uniform_market", [])
    for index, value in enumerate(uniform_values):
        ax.annotate(
            format_int_cs(int(round(value))),
            (x[index], value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color="#333333",
        )

    save_figure(fig, "h1_class_median_payouts.png")


def plot_h1_class_payout_compression(class_rows: list[dict[str, str]]) -> None:
    class_labels, scenario_labels, matrix = build_class_matrix(
        class_rows,
        "median_payout_compression_vs_uniform",
    )
    scenarios = sorted(matrix.keys(), key=scenario_order_key)
    x = np.arange(len(class_labels))

    # Узкий диапазон, чтобы малые отличия были видны.
    all_values = [value for values in matrix.values() for value in values]
    ymin = min(all_values)
    ymax = max(all_values)
    margin = max((ymax - ymin) * 0.25, 0.01)

    fig, ax = plt.subplots(figsize=(13.8, 6.4))

    for scenario in scenarios:
        color, marker = get_scenario_style(scenario)
        ax.plot(
            x,
            matrix[scenario],
            marker=marker,
            linewidth=2.2,
            markersize=6,
            label=scenario_labels[scenario],
            color=color,
        )

    ax.axhline(1.0, linestyle="--", linewidth=1.2, color="#4c78a8")
    ax.set_title("Komprese mediánu individuální výplaty vůči uniformnímu trhu", fontsize=16, fontweight="bold")
    ax.set_xlabel("Výherní třída")
    ax.set_ylabel("Poměr vůči uniformnímu trhu")
    ax.set_xticks(x)
    ax.set_xticklabels(class_labels)
    ax.set_ylim(ymin - margin, ymax + margin)
    ax.legend(loc="best")
    ax.grid(True, axis="y", alpha=0.25)

    save_figure(fig, "h1_class_payout_compression.png")


def plot_h1_class_winners(class_rows: list[dict[str, str]]) -> None:
    class_labels, scenario_labels, matrix = build_class_matrix(class_rows, "mean_winners_when_hit")
    scenarios = sorted(matrix.keys(), key=scenario_order_key)
    x = np.arange(len(class_labels))

    fig, ax = plt.subplots(figsize=(13.8, 6.8))

    for scenario in scenarios:
        color, marker = get_scenario_style(scenario)
        ax.plot(
            x,
            matrix[scenario],
            marker=marker,
            linewidth=2.2,
            markersize=6,
            label=scenario_labels[scenario],
            color=color,
        )

    ax.set_title("Průměrný počet vítězů při zásahu výherní třídy", fontsize=16, fontweight="bold")
    ax.set_xlabel("Výherní třída")
    ax.set_ylabel("Počet vítězů (log měřítko)")
    ax.set_xticks(x)
    ax.set_xticklabels(class_labels)
    ax.set_yscale("log")
    ax.legend(loc="upper left")
    ax.grid(True, axis="y", alpha=0.25)

    uniform_values = matrix.get("uniform_market", [])
    for index, value in enumerate(uniform_values):
        ax.annotate(
            format_float_cs(value, 2),
            (x[index], value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            color="#333333",
        )

    save_figure(fig, "h1_class_winners_when_hit.png")


def plot_h1_effective_support(summary_rows: list[dict[str, str]]) -> None:
    labels = [row["label_cs"] for row in summary_rows]
    values = [float(row["effective_ticket_support"]) for row in summary_rows]

    fig, ax = plt.subplots(figsize=(10.8, 6.2))
    bars = ax.bar(labels, values, color=FACULTY_COLOR)

    ax.set_title("Efektivní šířka trhu podle struktury výběru", fontsize=16, fontweight="bold")
    ax.set_xlabel("Profil trhu")
    ax.set_ylabel("Efektivní počet kombinací (log měřítko)")
    ax.set_yscale("log")
    ax.grid(True, axis="y", alpha=0.25)

    for bar in bars:
        value = bar.get_height()
        ax.annotate(
            format_int_cs(int(round(value))),
            (bar.get_x() + bar.get_width() / 2, value),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=9,
        )

    save_figure(fig, "h1_effective_support.png")


def main() -> None:
    summary_rows = sort_summary_rows(
        load_csv_rows(find_latest("h1_choice_bias_summary_*.csv"))
    )
    class_rows = sort_class_rows(
        load_csv_rows(find_latest("h1_choice_bias_class_summary_*.csv"))
    )

    plot_h1_overall_winner_payouts(summary_rows)
    plot_h1_return_variance(summary_rows)
    plot_h1_class_median_payouts(class_rows)
    plot_h1_class_payout_compression(class_rows)
    plot_h1_class_winners(class_rows)
    plot_h1_effective_support(summary_rows)

    print(f"Plots saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()