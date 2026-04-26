"""Experiment definitions for chapter 3.

This module defines three experiment groups:

1. Probability of reaching positive net-result thresholds
2. Simulated waiting time until the first jackpot
3. RTP comparison of uniform vs realistic market models at different market sizes
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfitThresholdScenario:
    """Scenario for experiment 1."""

    name: str
    label_cs: str
    description: str
    draws: int
    market_model: str
    tickets_sold_per_draw: int
    main_numbers: list[int]
    euro_numbers: list[int]
    repetitions: int
    base_seed: int


@dataclass(frozen=True)
class JackpotExperimentConfig:
    """Configuration for experiment 2."""

    name: str
    label_cs: str
    description: str
    jackpot_probability: float
    ticket_price_eur: float
    assumed_jackpot_payout_eur: float
    repetitions: int
    seed: int


@dataclass(frozen=True)
class RtpMarketScenario:
    """Scenario for experiment 3."""

    name: str
    label_cs: str
    description: str
    draws: int
    market_model: str
    tickets_sold_per_draw: int
    main_numbers: list[int]
    euro_numbers: list[int]
    repetitions: int
    base_seed: int


BASELINE_MAIN = [7, 11, 13, 21, 23]
BASELINE_EURO = [1, 2]

PROFIT_THRESHOLDS_EUR = [
    0,
    10,
    100,
    1_000,
    10_000,
    100_000,
    1_000_000,
    10_000_000,
]

PROFIT_THRESHOLD_SCENARIOS: list[ProfitThresholdScenario] = [
    ProfitThresholdScenario(
        name="profit_realistic_100",
        label_cs="100",
        description="Realistický model, 100 odehraných tiketů.",
        draws=100,
        market_model="realistic",
        tickets_sold_per_draw=1_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=2026,
    ),
    ProfitThresholdScenario(
        name="profit_realistic_1000",
        label_cs="1 000",
        description="Realistický model, 1 000 odehraných tiketů.",
        draws=1_000,
        market_model="realistic",
        tickets_sold_per_draw=1_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=3026,
    ),
    ProfitThresholdScenario(
        name="profit_realistic_10000",
        label_cs="10 000",
        description="Realistický model, 10 000 odehraných tiketů.",
        draws=10_000,
        market_model="realistic",
        tickets_sold_per_draw=1_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=4026,
    ),
    ProfitThresholdScenario(
        name="profit_realistic_100000",
        label_cs="100 000",
        description="Realistický model, 100 000 odehraných tiketů.",
        draws=100_000,
        market_model="realistic",
        tickets_sold_per_draw=1_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=5026,
    ),
    ProfitThresholdScenario(
        name="profit_realistic_1000000",
        label_cs="1 000 000",
        description="Realistický model, 1 000 000 odehraných tiketů.",
        draws=1_000_000,
        market_model="realistic",
        tickets_sold_per_draw=1_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=6026,
    ),
]

JACKPOT_EXPERIMENT = JackpotExperimentConfig(
    name="jackpot_waiting_time",
    label_cs="Jackpot",
    description=(
        "Simulace počtu tiketů do prvního jackpotu při pravděpodobnosti "
        "1 : 139 838 160 a s předpokladem výplaty 120 mil. €."
    ),
    jackpot_probability=1 / 139_838_160,
    ticket_price_eur=2.0,
    assumed_jackpot_payout_eur=120_000_000.0,
    repetitions=10_000,
    seed=7026,
)

RTP_MARKET_SCENARIOS: list[RtpMarketScenario] = [
    RtpMarketScenario(
        name="rtp_uniform_10k",
        label_cs="10 000",
        description="Rovnoměrný model, 10 000 prodaných tiketů.",
        draws=50_000,
        market_model="uniform",
        tickets_sold_per_draw=10_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=8026,
    ),
    RtpMarketScenario(
        name="rtp_realistic_10k",
        label_cs="10 000",
        description="Realistický model, 10 000 prodaných tiketů.",
        draws=50_000,
        market_model="realistic",
        tickets_sold_per_draw=10_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=9026,
    ),
    RtpMarketScenario(
        name="rtp_uniform_100k",
        label_cs="100 000",
        description="Rovnoměrný model, 100 000 prodaných tiketů.",
        draws=50_000,
        market_model="uniform",
        tickets_sold_per_draw=100_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=10026,
    ),
    RtpMarketScenario(
        name="rtp_realistic_100k",
        label_cs="100 000",
        description="Realistický model, 100 000 prodaných tiketů.",
        draws=50_000,
        market_model="realistic",
        tickets_sold_per_draw=100_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=11026,
    ),
    RtpMarketScenario(
        name="rtp_uniform_1m",
        label_cs="1 000 000",
        description="Rovnoměrný model, 1 000 000 prodaných tiketů.",
        draws=50_000,
        market_model="uniform",
        tickets_sold_per_draw=1_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=12026,
    ),
    RtpMarketScenario(
        name="rtp_realistic_1m",
        label_cs="1 000 000",
        description="Realistický model, 1 000 000 prodaných tiketů.",
        draws=50_000,
        market_model="realistic",
        tickets_sold_per_draw=1_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=13026,
    ),
    RtpMarketScenario(
        name="rtp_uniform_10m",
        label_cs="10 000 000",
        description="Rovnoměrný model, 10 000 000 prodaných tiketů.",
        draws=50_000,
        market_model="uniform",
        tickets_sold_per_draw=10_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=14026,
    ),
    RtpMarketScenario(
        name="rtp_realistic_10m",
        label_cs="10 000 000",
        description="Realistický model, 10 000 000 prodaných tiketů.",
        draws=50_000,
        market_model="realistic",
        tickets_sold_per_draw=10_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=15026,
    ),
    RtpMarketScenario(
        name="rtp_uniform_100m",
        label_cs="100 000 000",
        description="Rovnoměrný model, 100 000 000 prodaných tiketů.",
        draws=50_000,
        market_model="uniform",
        tickets_sold_per_draw=100_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=16026,
    ),
    RtpMarketScenario(
        name="rtp_realistic_100m",
        label_cs="100 000 000",
        description="Realistický model, 100 000 000 prodaných tiketů.",
        draws=50_000,
        market_model="realistic",
        tickets_sold_per_draw=100_000_000,
        main_numbers=BASELINE_MAIN,
        euro_numbers=BASELINE_EURO,
        repetitions=1000,
        base_seed=17026,
    ),
]