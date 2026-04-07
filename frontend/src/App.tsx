import { useMemo, useState } from "react";
import { runSimulation } from "./api/simulation";
import type {
  PrizeClassSummary,
  SimulationResponse,
} from "./types/simulation";

type Language = "en" | "cs";
type MarketModel = "uniform" | "realistic";

type TranslationSet = {
  title: string;
  languageLabel: string;
  yourTicket: string;
  mainNumbers: string;
  euroNumbers: string;
  generateRandomTicket: string;
  otherPlayers: string;
  otherPlayersBehavior: string;
  randomSelection: string;
  preferenceBasedSelection: string;
  ticketsSoldPerDraw: string;
  sessionControls: string;
  buy1: string;
  buy10: string;
  buy100: string;
  buyCustom: string;
  reset: string;
  ticketsPlayed: string;
  winningTickets: string;
  totalSpent: string;
  totalWon: string;
  netResult: string;
  rtp: string;
  yourTicketShort: string;
  simulationResults: string;
  noResultsChart: string;
  prizeDistribution: string;
  category: string;
  count: string;
  avgActualPayout: string;
  actualTotalWon: string;
  noResultsTable: string;
  ticketsLabel: string;
  disclaimer: string;
  validationMainCount: string;
  validationEuroCount: string;
  validationMainIntegers: string;
  validationEuroIntegers: string;
  validationMainRange: string;
  validationEuroRange: string;
  validationMainUnique: string;
  validationEuroUnique: string;
  validationBuyPositive: string;
  validationTicketsSoldPositive: string;
  loadingError: string;
};

const translations: Record<Language, TranslationSet> = {
  en: {
    title: "Eurojackpot Simulator",
    languageLabel: "Language",
    yourTicket: "Your ticket",
    mainNumbers: "Main numbers",
    euroNumbers: "Euro numbers",
    generateRandomTicket: "Generate random ticket",
    otherPlayers: "Other players",
    otherPlayersBehavior: "Other players' behavior",
    randomSelection: "Random selection",
    preferenceBasedSelection: "Preference-based selection",
    ticketsSoldPerDraw: "Tickets sold per draw",
    sessionControls: "Session controls",
    buy1: "Buy 1",
    buy10: "Buy 10",
    buy100: "Buy 100",
    buyCustom: "Buy custom",
    reset: "Reset",
    ticketsPlayed: "Tickets played",
    winningTickets: "Winning tickets",
    totalSpent: "Total spent",
    totalWon: "Total won",
    netResult: "Net result",
    rtp: "RTP",
    yourTicketShort: "Your ticket",
    simulationResults: "Simulation results",
    noResultsChart: "No results yet. Buy tickets to see the distribution.",
    prizeDistribution: "Prize distribution",
    category: "Category",
    count: "Count",
    avgActualPayout: "Avg actual payout",
    actualTotalWon: "Actual total won",
    noResultsTable: "No results yet. Buy tickets to start the session.",
    ticketsLabel: "tickets",
    disclaimer:
      "Disclaimer: This website is a simulation created for educational and research purposes only. It is not affiliated with the official Eurojackpot lottery and should not be used for gambling decisions.",
    validationMainCount: "Main numbers must contain exactly 5 values.",
    validationEuroCount: "Euro numbers must contain exactly 2 values.",
    validationMainIntegers: "All main numbers must be integers.",
    validationEuroIntegers: "All euro numbers must be integers.",
    validationMainRange: "Main numbers must be between 1 and 50.",
    validationEuroRange: "Euro numbers must be between 1 and 12.",
    validationMainUnique: "Main numbers must be unique.",
    validationEuroUnique: "Euro numbers must be unique.",
    validationBuyPositive: "The number of tickets to buy must be a positive integer.",
    validationTicketsSoldPositive: "Tickets sold per draw must be a positive integer.",
    loadingError: "Unexpected error while running simulation.",
  },
  cs: {
    title: "Simulátor Eurojackpotu",
    languageLabel: "Jazyk",
    yourTicket: "Váš tiket",
    mainNumbers: "Hlavní čísla",
    euroNumbers: "Euro čísla",
    generateRandomTicket: "Vygenerovat náhodný tiket",
    otherPlayers: "Ostatní hráči",
    otherPlayersBehavior: "Chování ostatních hráčů",
    randomSelection: "Náhodný výběr",
    preferenceBasedSelection: "Výběr podle preferencí",
    ticketsSoldPerDraw: "Počet prodaných tiketů na losování",
    sessionControls: "Ovládání simulace",
    buy1: "Koupit 1",
    buy10: "Koupit 10",
    buy100: "Koupit 100",
    buyCustom: "Koupit vlastní počet",
    reset: "Reset",
    ticketsPlayed: "Odehrané tikety",
    winningTickets: "Výherní tikety",
    totalSpent: "Celkové náklady",
    totalWon: "Celková výhra",
    netResult: "Čistý výsledek",
    rtp: "RTP",
    yourTicketShort: "Váš tiket",
    simulationResults: "Výsledky simulace",
    noResultsChart:
      "Zatím nejsou k dispozici žádné výsledky. Kupte tikety pro zobrazení rozdělení.",
    prizeDistribution: "Rozdělení výher",
    category: "Kategorie",
    count: "Počet",
    avgActualPayout: "Průměrná výplata",
    actualTotalWon: "Celkově vyhráno",
    noResultsTable:
      "Zatím nejsou k dispozici žádné výsledky. Kupte tikety pro zahájení simulace.",
    ticketsLabel: "tiketů",
    disclaimer:
      "Upozornění: Tato webová stránka je simulace vytvořená pouze pro vzdělávací a výzkumné účely. Není spojena s oficiální loterií Eurojackpot a neměla by být používána pro rozhodování o hazardních hrách.",
    validationMainCount: "Hlavní čísla musí obsahovat přesně 5 hodnot.",
    validationEuroCount: "Euro čísla musí obsahovat přesně 2 hodnoty.",
    validationMainIntegers: "Všechna hlavní čísla musí být celá čísla.",
    validationEuroIntegers: "Všechna euro čísla musí být celá čísla.",
    validationMainRange: "Hlavní čísla musí být v rozsahu 1 až 50.",
    validationEuroRange: "Euro čísla musí být v rozsahu 1 až 12.",
    validationMainUnique: "Hlavní čísla se nesmí opakovat.",
    validationEuroUnique: "Euro čísla se nesmí opakovat.",
    validationBuyPositive: "Počet kupovaných tiketů musí být kladné celé číslo.",
    validationTicketsSoldPositive: "Počet prodaných tiketů musí být kladné celé číslo.",
    loadingError: "Při spuštění simulace došlo k neočekávané chybě.",
  },
};

function getUniqueRandomNumbers(count: number, min: number, max: number): number[] {
  const numbers = new Set<number>();

  while (numbers.size < count) {
    const value = Math.floor(Math.random() * (max - min + 1)) + min;
    numbers.add(value);
  }

  return Array.from(numbers).sort((a, b) => a - b);
}

function parseNumericInput(value: string): number {
  if (value.trim() === "") {
    return NaN;
  }

  return Number(value);
}

function parseIntegerInputWithSpaces(value: string): number {
  const digitsOnly = value.replace(/\s/g, "").replace(/[^\d]/g, "");

  if (digitsOnly === "") {
    return NaN;
  }

  return Number(digitsOnly);
}

function formatIntegerInput(value: number): string {
  if (!Number.isFinite(value)) {
    return "";
  }

  return new Intl.NumberFormat("cs-CZ", {
    maximumFractionDigits: 0,
  }).format(value);
}

function safeNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function formatInteger(value: number): string {
  return new Intl.NumberFormat("cs-CZ", {
    maximumFractionDigits: 0,
  }).format(value);
}

function formatMoney(value: number): string {
  return `${new Intl.NumberFormat("cs-CZ", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)} €`;
}

function formatChartMoney(value: number): string {
  return `${new Intl.NumberFormat("cs-CZ", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)} €`;
}

function formatRatio(value: number): string {
  return new Intl.NumberFormat("cs-CZ", {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}

function validateTicket(
  mainNumbers: number[],
  euroNumbers: number[],
  t: TranslationSet
): string[] {
  const errors: string[] = [];

  if (mainNumbers.length !== 5) {
    errors.push(t.validationMainCount);
  }

  if (euroNumbers.length !== 2) {
    errors.push(t.validationEuroCount);
  }

  if (mainNumbers.some((n) => !Number.isInteger(n))) {
    errors.push(t.validationMainIntegers);
  }

  if (euroNumbers.some((n) => !Number.isInteger(n))) {
    errors.push(t.validationEuroIntegers);
  }

  if (mainNumbers.some((n) => n < 1 || n > 50)) {
    errors.push(t.validationMainRange);
  }

  if (euroNumbers.some((n) => n < 1 || n > 12)) {
    errors.push(t.validationEuroRange);
  }

  if (new Set(mainNumbers).size !== mainNumbers.length) {
    errors.push(t.validationMainUnique);
  }

  if (new Set(euroNumbers).size !== euroNumbers.length) {
    errors.push(t.validationEuroUnique);
  }

  return errors;
}

type AccumulatedResult = {
  tickets_played: number;
  winning_tickets: number;
  total_spent: number;
  total_won: number;
  prize_classes: PrizeClassSummary[];
};

function createEmptyAccumulatedResult(): AccumulatedResult {
  return {
    tickets_played: 0,
    winning_tickets: 0,
    total_spent: 0,
    total_won: 0,
    prize_classes: [],
  };
}

function mergePrizeClasses(
  current: PrizeClassSummary[],
  incoming: PrizeClassSummary[]
): PrizeClassSummary[] {
  const map = new Map<string, PrizeClassSummary>();

  for (const item of current) {
    map.set(item.key, { ...item });
  }

  for (const item of incoming) {
    const existing = map.get(item.key);

    if (!existing) {
      map.set(item.key, { ...item });
      continue;
    }

    const mergedCount = safeNumber(existing.count) + safeNumber(item.count);
    const mergedActualTotalWon =
      safeNumber(existing.actual_total_won) + safeNumber(item.actual_total_won);

    const mergedAverageActualPayout =
      mergedCount > 0 ? mergedActualTotalWon / mergedCount : 0;

    map.set(item.key, {
      key: item.key,
      label: item.label,
      count: mergedCount,
      average_class_fund: 0,
      average_actual_payout: mergedAverageActualPayout,
      actual_total_won: mergedActualTotalWon,
    });
  }

  return Array.from(map.values());
}

function App() {
  const [language, setLanguage] = useState<Language>("en");
  const t = translations[language];

  const [marketModel, setMarketModel] = useState<MarketModel>("uniform");
  const [ticketsSoldPerDraw, setTicketsSoldPerDraw] = useState(1000000);

  const [mainNumbers, setMainNumbers] = useState<number[]>([7, 11, 13, 21, 23]);
  const [euroNumbers, setEuroNumbers] = useState<number[]>([1, 2]);

  const [customBuyAmount, setCustomBuyAmount] = useState(1000);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const [sessionResult, setSessionResult] = useState<AccumulatedResult>(
    createEmptyAccumulatedResult()
  );

  const ticketErrors = useMemo(
    () => validateTicket(mainNumbers, euroNumbers, t),
    [mainNumbers, euroNumbers, t]
  );

  const updateMainNumber = (index: number, rawValue: string) => {
    const next = [...mainNumbers];
    next[index] = parseNumericInput(rawValue);
    setMainNumbers(next);
  };

  const updateEuroNumber = (index: number, rawValue: string) => {
    const next = [...euroNumbers];
    next[index] = parseNumericInput(rawValue);
    setEuroNumbers(next);
  };

  const handleRandomTicket = () => {
    setMainNumbers(getUniqueRandomNumbers(5, 1, 50));
    setEuroNumbers(getUniqueRandomNumbers(2, 1, 12));
    setErrorMessage("");
  };

  const handleReset = () => {
    setSessionResult(createEmptyAccumulatedResult());
    setErrorMessage("");
  };

  const buyTickets = async (drawsToBuy: number) => {
    setErrorMessage("");

    if (ticketErrors.length > 0) {
      setErrorMessage(ticketErrors.join(" "));
      return;
    }

    if (!Number.isInteger(drawsToBuy) || drawsToBuy < 1) {
      setErrorMessage(t.validationBuyPositive);
      return;
    }

    if (!Number.isInteger(ticketsSoldPerDraw) || ticketsSoldPerDraw < 1) {
      setErrorMessage(t.validationTicketsSoldPositive);
      return;
    }

    setLoading(true);

    try {
      const res: SimulationResponse = await runSimulation({
        draws: drawsToBuy,
        market_model: marketModel,
        tickets_sold_per_draw: ticketsSoldPerDraw,
        user_ticket: {
          main_numbers: [...mainNumbers].sort((a, b) => a - b),
          euro_numbers: [...euroNumbers].sort((a, b) => a - b),
        },
      });

      setSessionResult((prev) => ({
        tickets_played: prev.tickets_played + safeNumber(res.tickets_played),
        winning_tickets: prev.winning_tickets + safeNumber(res.winning_tickets),
        total_spent: prev.total_spent + safeNumber(res.total_spent),
        total_won: prev.total_won + safeNumber(res.total_won),
        prize_classes: mergePrizeClasses(prev.prize_classes, res.prize_classes ?? []),
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : t.loadingError;
      setErrorMessage(message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const netResult = sessionResult.total_won - sessionResult.total_spent;
  const rtp =
    sessionResult.total_spent > 0
      ? sessionResult.total_won / sessionResult.total_spent
      : 0;

  const sortedPrizeClasses = [...sessionResult.prize_classes].sort(
    (a, b) => safeNumber(b.actual_total_won) - safeNumber(a.actual_total_won)
  );

  const maxBarValue = Math.max(
    1,
    ...sortedPrizeClasses.map((item) => safeNumber(item.actual_total_won))
  );

  return (
    <div className="page">
      <div className="container">
        <header className="topbar">
          <h1 className="page-title">{t.title}</h1>

          <div className="language-switcher">
            <span className="language-label">{t.languageLabel}</span>
            <div className="language-buttons">
              <button
                className={`lang-btn ${language === "en" ? "active" : ""}`}
                onClick={() => setLanguage("en")}
                type="button"
              >
                EN
              </button>
              <button
                className={`lang-btn ${language === "cs" ? "active" : ""}`}
                onClick={() => setLanguage("cs")}
                type="button"
              >
                CS
              </button>
            </div>
          </div>
        </header>

        <div className="layout">
          <aside className="sidebar">
            <section className="card">
              <h2 className="card-title">{t.yourTicket}</h2>

              <div className="field-label">{t.mainNumbers}</div>
              <div className="numbers-grid numbers-grid-main">
                {mainNumbers.map((number, index) => (
                  <input
                    key={`main-${index}`}
                    type="text"
                    inputMode="numeric"
                    value={Number.isNaN(number) ? "" : number}
                    onChange={(e) => updateMainNumber(index, e.target.value)}
                    className="number-input"
                  />
                ))}
              </div>

              <div className="field-label">{t.euroNumbers}</div>
              <div className="numbers-grid numbers-grid-euro">
                {euroNumbers.map((number, index) => (
                  <input
                    key={`euro-${index}`}
                    type="text"
                    inputMode="numeric"
                    value={Number.isNaN(number) ? "" : number}
                    onChange={(e) => updateEuroNumber(index, e.target.value)}
                    className="number-input"
                  />
                ))}
              </div>

              <button onClick={handleRandomTicket} className="secondary-button">
                {t.generateRandomTicket}
              </button>
            </section>

            <section className="card">
              <h2 className="card-title">{t.otherPlayers}</h2>

              <div className="field-block">
                <label className="field-label">{t.otherPlayersBehavior}</label>
                <select
                  value={marketModel}
                  onChange={(e) => setMarketModel(e.target.value as MarketModel)}
                  className="select-input"
                >
                  <option value="uniform">{t.randomSelection}</option>
                  <option value="realistic">{t.preferenceBasedSelection}</option>
                </select>
              </div>

              <div className="field-block">
                <label className="field-label">{t.ticketsSoldPerDraw}</label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={formatIntegerInput(ticketsSoldPerDraw)}
                  onChange={(e) =>
                    setTicketsSoldPerDraw(parseIntegerInputWithSpaces(e.target.value))
                  }
                  className="text-input"
                />
              </div>
            </section>
          </aside>

          <main className="content">
            <section className="card">
              <div className="controls-header">
                <h2 className="card-title">{t.sessionControls}</h2>
              </div>

              <div className="controls-row">
                <button
                  onClick={() => buyTickets(1)}
                  disabled={loading}
                  className="primary-button"
                >
                  {t.buy1}
                </button>
                <button
                  onClick={() => buyTickets(10)}
                  disabled={loading}
                  className="primary-button"
                >
                  {t.buy10}
                </button>
                <button
                  onClick={() => buyTickets(100)}
                  disabled={loading}
                  className="primary-button"
                >
                  {t.buy100}
                </button>

                <input
                  type="text"
                  inputMode="numeric"
                  value={formatIntegerInput(customBuyAmount)}
                  onChange={(e) =>
                    setCustomBuyAmount(parseIntegerInputWithSpaces(e.target.value))
                  }
                  className="custom-buy-input"
                />

                <button
                  onClick={() => buyTickets(customBuyAmount)}
                  disabled={loading}
                  className="primary-button"
                >
                  {t.buyCustom}
                </button>

                <button onClick={handleReset} disabled={loading} className="danger-button">
                  {t.reset}
                </button>
              </div>

              {errorMessage && <div className="error-box">{errorMessage}</div>}
            </section>

            <section className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">{t.ticketsPlayed}</div>
                <div className="metric-value">{formatInteger(sessionResult.tickets_played)}</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">{t.winningTickets}</div>
                <div className="metric-value">{formatInteger(sessionResult.winning_tickets)}</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">{t.totalSpent}</div>
                <div className="metric-value">{formatMoney(sessionResult.total_spent)}</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">{t.totalWon}</div>
                <div className="metric-value">{formatMoney(sessionResult.total_won)}</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">{t.netResult}</div>
                <div className={`metric-value ${netResult >= 0 ? "positive" : "negative"}`}>
                  {formatMoney(netResult)}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">{t.rtp}</div>
                <div className="metric-value">{formatRatio(rtp)}</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">{t.otherPlayersBehavior}</div>
                <div className="metric-value metric-text">
                  {marketModel === "uniform" ? t.randomSelection : t.preferenceBasedSelection}
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">{t.yourTicketShort}</div>
                <div className="metric-value metric-ticket">
                  {mainNumbers.join(", ")} | {euroNumbers.join(", ")}
                </div>
              </div>
            </section>

            <section className="card">
              <h2 className="card-title">{t.simulationResults}</h2>

              <div className="chart-list">
                {sortedPrizeClasses.length === 0 && (
                  <div className="empty-state">{t.noResultsChart}</div>
                )}

                {sortedPrizeClasses.map((item) => {
                  const totalWon = safeNumber(item.actual_total_won);
                  const ticketCount = safeNumber(item.count);
                  const barWidth = `${(totalWon / maxBarValue) * 100}%`;

                  return (
                    <div key={`bar-${item.key}`} className="chart-row">
                      <div className="chart-label">{item.label}</div>

                      <div className="chart-middle">
                        <div className="chart-tickets-line">
                          {ticketCount > 0 ? (
                            <span className="chart-tickets-note">
                              {formatInteger(ticketCount)} {t.ticketsLabel}
                            </span>
                          ) : (
                            <span className="chart-tickets-note chart-tickets-note-empty">
                              &nbsp;
                            </span>
                          )}
                        </div>

                        <div className="chart-track">
                          <div className="chart-bar" style={{ width: barWidth }} />
                        </div>
                      </div>

                      <div className="chart-value">{formatChartMoney(totalWon)}</div>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="card">
              <h2 className="card-title">{t.prizeDistribution}</h2>

              <div className="table-wrapper">
                <table className="results-table">
                  <thead>
                    <tr>
                      <th>{t.category}</th>
                      <th>{t.count}</th>
                      <th>{t.avgActualPayout}</th>
                      <th>{t.actualTotalWon}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPrizeClasses.map((item) => (
                      <tr key={item.key}>
                        <td>{item.label}</td>
                        <td>{formatInteger(safeNumber(item.count))}</td>
                        <td>{formatMoney(safeNumber(item.average_actual_payout))}</td>
                        <td>{formatMoney(safeNumber(item.actual_total_won))}</td>
                      </tr>
                    ))}
                    {sortedPrizeClasses.length === 0 && (
                      <tr>
                        <td colSpan={4} className="empty-table-cell">
                          {t.noResultsTable}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </main>
        </div>

        <footer className="footer-disclaimer">{t.disclaimer}</footer>
      </div>
    </div>
  );
}

export default App;