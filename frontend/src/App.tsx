/**
 * Main frontend screen for the Eurojackpot simulator.
 *
 * The component keeps the current ticket settings, sends batched buy requests
 * to the backend, accumulates returned results locally, and renders the main
 * dashboard cards, chart, and table.
 */

import { useMemo, useState } from "react";
import { runSimulation } from "./api/simulation";
import type {
  PrizeClassSummary,
  SimulationResponse,
} from "./types/simulation";

/** Generate a sorted list of unique random integers for quick ticket creation. */
function getUniqueRandomNumbers(count: number, min: number, max: number): number[] {
  const numbers = new Set<number>();

  while (numbers.size < count) {
    const value = Math.floor(Math.random() * (max - min + 1)) + min;
    numbers.add(value);
  }

  return Array.from(numbers).sort((a, b) => a - b);
}

/** Convert text input into a number while preserving an empty field as NaN. */
function parseNumericInput(value: string): number {
  if (value.trim() === "") {
    return NaN;
  }

  return Number(value);
}

/** Protect rendering code from undefined / null / non-numeric values. */
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

function formatShortMoney(value: number): string {
  const abs = Math.abs(value);

  if (abs >= 1_000_000_000) {
    return `${new Intl.NumberFormat("cs-CZ", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value / 1_000_000_000)}B €`;
  }
  if (abs >= 1_000_000) {
    return `${new Intl.NumberFormat("cs-CZ", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value / 1_000_000)}M €`;
  }
  if (abs >= 1_000) {
    return `${new Intl.NumberFormat("cs-CZ", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value / 1_000)}K €`;
  }

  return `${new Intl.NumberFormat("cs-CZ", {
    maximumFractionDigits: 0,
  }).format(value)} €`;
}

function formatRatio(value: number): string {
  return new Intl.NumberFormat("cs-CZ", {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}

/** Validate the user ticket before a request is sent to the backend. */
function validateTicket(mainNumbers: number[], euroNumbers: number[]): string[] {
  const errors: string[] = [];

  if (mainNumbers.length !== 5) {
    errors.push("Main numbers must contain exactly 5 values.");
  }

  if (euroNumbers.length !== 2) {
    errors.push("Euro numbers must contain exactly 2 values.");
  }

  if (mainNumbers.some((n) => !Number.isInteger(n))) {
    errors.push("All main numbers must be integers.");
  }

  if (euroNumbers.some((n) => !Number.isInteger(n))) {
    errors.push("All euro numbers must be integers.");
  }

  if (mainNumbers.some((n) => n < 1 || n > 50)) {
    errors.push("Main numbers must be between 1 and 50.");
  }

  if (euroNumbers.some((n) => n < 1 || n > 12)) {
    errors.push("Euro numbers must be between 1 and 12.");
  }

  if (new Set(mainNumbers).size !== mainNumbers.length) {
    errors.push("Main numbers must be unique.");
  }

  if (new Set(euroNumbers).size !== euroNumbers.length) {
    errors.push("Euro numbers must be unique.");
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

/** Create a clean session state used both on first load and after reset. */
function createEmptyAccumulatedResult(): AccumulatedResult {
  return {
    tickets_played: 0,
    winning_tickets: 0,
    total_spent: 0,
    total_won: 0,
    prize_classes: [],
  };
}

/**
 * Merge the latest batch result into the running frontend session.
 *
 * The backend returns per-request summaries. The frontend accumulates them so
 * the user can keep buying tickets until Reset is pressed.
 */
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

function cardStyle(): React.CSSProperties {
  return {
    background: "#ffffff",
    border: "1px solid #e5eaf0",
    borderRadius: "18px",
    boxShadow: "0 8px 24px rgba(15, 23, 42, 0.05)",
  };
}

function primaryButtonStyle(disabled: boolean): React.CSSProperties {
  return {
    padding: "10px 16px",
    cursor: disabled ? "not-allowed" : "pointer",
    backgroundColor: disabled ? "#98a2b3" : "#111827",
    color: "#ffffff",
    border: "none",
    borderRadius: "12px",
    fontSize: "14px",
    fontWeight: 700,
    transition: "0.2s ease",
    whiteSpace: "nowrap",
  };
}

function secondaryButtonStyle(): React.CSSProperties {
  return {
    padding: "10px 14px",
    cursor: "pointer",
    backgroundColor: "#f1f5f9",
    color: "#0f172a",
    border: "1px solid #d8e0ea",
    borderRadius: "12px",
    fontSize: "14px",
    fontWeight: 700,
  };
}

function dangerButtonStyle(disabled: boolean): React.CSSProperties {
  return {
    padding: "10px 16px",
    cursor: disabled ? "not-allowed" : "pointer",
    backgroundColor: disabled ? "#e7a3a3" : "#dc2626",
    color: "#ffffff",
    border: "none",
    borderRadius: "12px",
    fontSize: "14px",
    fontWeight: 700,
    whiteSpace: "nowrap",
  };
}

function metricCardStyle(): React.CSSProperties {
  return {
    ...cardStyle(),
    padding: "14px 16px",
    minHeight: "78px",
  };
}

/** Render the complete simulator UI and orchestrate user actions. */
function App() {
  const [marketModel, setMarketModel] = useState<"uniform" | "realistic">("uniform");
  const [ticketsSoldPerDraw, setTicketsSoldPerDraw] = useState(10000000);

  const [mainNumbers, setMainNumbers] = useState<number[]>([7, 11, 13, 21, 23]);
  const [euroNumbers, setEuroNumbers] = useState<number[]>([1, 2]);

  const [customBuyAmount, setCustomBuyAmount] = useState(1000);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const [sessionResult, setSessionResult] = useState<AccumulatedResult>(
    createEmptyAccumulatedResult()
  );

  // Recalculate validation errors only when the ticket changes.
  const ticketErrors = useMemo(
    () => validateTicket(mainNumbers, euroNumbers),
    [mainNumbers, euroNumbers]
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

  // Replace the current manual ticket with a quick random ticket.
  const handleRandomTicket = () => {
    setMainNumbers(getUniqueRandomNumbers(5, 1, 50));
    setEuroNumbers(getUniqueRandomNumbers(2, 1, 12));
    setErrorMessage("");
  };

  // Clear the accumulated session while keeping the chosen ticket and settings.
  const handleReset = () => {
    setSessionResult(createEmptyAccumulatedResult());
    setErrorMessage("");
  };

  /**
   * Buy one batch of tickets.
   *
   * The backend simulates `drawsToBuy` draws using the currently selected
   * ticket. The returned totals are then merged into the session state.
   */
  const buyTickets = async (drawsToBuy: number) => {
    setErrorMessage("");

    if (ticketErrors.length > 0) {
      setErrorMessage(ticketErrors.join(" "));
      return;
    }

    if (!Number.isInteger(drawsToBuy) || drawsToBuy < 1) {
      setErrorMessage("The number of tickets to buy must be a positive integer.");
      return;
    }

    if (!Number.isInteger(ticketsSoldPerDraw) || ticketsSoldPerDraw < 1) {
      setErrorMessage("Tickets sold per draw must be a positive integer.");
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
      const message =
        err instanceof Error ? err.message : "Unexpected error while running simulation.";
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

  // Order chart bars and table rows by total won so the most important classes
  // appear first.
  const sortedPrizeClasses = [...sessionResult.prize_classes].sort(
    (a, b) => safeNumber(b.actual_total_won) - safeNumber(a.actual_total_won)
  );

  const maxBarValue = Math.max(
    1,
    ...sortedPrizeClasses.map((item) => safeNumber(item.actual_total_won))
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #f8fafc 0%, #eef3f8 100%)",
        padding: "20px",
        fontFamily:
          "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        color: "#0f172a",
      }}
    >
      <div
        style={{
          maxWidth: "1380px",
          margin: "0 auto",
        }}
      >
        <div style={{ marginBottom: "18px" }}>
          <h1
            style={{
              margin: 0,
              fontSize: "34px",
              fontWeight: 800,
              letterSpacing: "-0.03em",
              color: "#0f172a",
            }}
          >
            Eurojackpot Simulator
          </h1>
          <p
            style={{
              marginTop: "8px",
              marginBottom: 0,
              color: "#475569",
              fontSize: "15px",
            }}
          >
            Buy tickets in batches, keep the session running, and reset only when you
            want to start over.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "320px minmax(0, 1fr)",
            gap: "18px",
            alignItems: "start",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Detailed table for the same distribution shown in the chart. */}
            <div style={{ ...cardStyle(), padding: "18px" }}>
              <h2
                style={{
                  marginTop: 0,
                  marginBottom: "14px",
                  fontSize: "20px",
                  color: "#0f172a",
                }}
              >
                Your ticket
              </h2>

              <div style={{ marginBottom: "8px", color: "#334155", fontWeight: 700 }}>
                Main numbers
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(5, 1fr)",
                  gap: "8px",
                  marginBottom: "14px",
                }}
              >
                {mainNumbers.map((number, index) => (
                  <input
                    key={`main-${index}`}
                    type="number"
                    value={Number.isNaN(number) ? "" : number}
                    min={1}
                    max={50}
                    onChange={(e) => updateMainNumber(index, e.target.value)}
                    style={{
                      padding: "10px",
                      width: "100%",
                      borderRadius: "12px",
                      border: "1px solid #d6dee8",
                      background: "#f8fafc",
                      fontSize: "14px",
                      color: "#0f172a",
                      boxSizing: "border-box",
                    }}
                  />
                ))}
              </div>

              <div style={{ marginBottom: "8px", color: "#334155", fontWeight: 700 }}>
                Euro numbers
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, 1fr)",
                  gap: "8px",
                  marginBottom: "14px",
                }}
              >
                {euroNumbers.map((number, index) => (
                  <input
                    key={`euro-${index}`}
                    type="number"
                    value={Number.isNaN(number) ? "" : number}
                    min={1}
                    max={12}
                    onChange={(e) => updateEuroNumber(index, e.target.value)}
                    style={{
                      padding: "10px",
                      width: "100%",
                      borderRadius: "12px",
                      border: "1px solid #d6dee8",
                      background: "#f8fafc",
                      fontSize: "14px",
                      color: "#0f172a",
                      boxSizing: "border-box",
                    }}
                  />
                ))}
              </div>

              <button onClick={handleRandomTicket} style={secondaryButtonStyle()}>
                Generate random ticket
              </button>
            </div>

            {/* Detailed table for the same distribution shown in the chart. */}
            <div style={{ ...cardStyle(), padding: "18px" }}>
              <h2
                style={{
                  marginTop: 0,
                  marginBottom: "14px",
                  fontSize: "20px",
                  color: "#0f172a",
                }}
              >
                Market settings
              </h2>

              <div style={{ marginBottom: "14px" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    color: "#334155",
                    fontWeight: 700,
                  }}
                >
                  Market model
                </label>
                <select
                  value={marketModel}
                  onChange={(e) =>
                    setMarketModel(e.target.value as "uniform" | "realistic")
                  }
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "12px",
                    border: "1px solid #d6dee8",
                    background: "#f8fafc",
                    fontSize: "14px",
                    color: "#0f172a",
                  }}
                >
                  <option value="uniform">uniform</option>
                  <option value="realistic">realistic</option>
                </select>
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    color: "#334155",
                    fontWeight: 700,
                  }}
                >
                  Tickets sold per draw
                </label>
                <input
                  type="number"
                  value={Number.isNaN(ticketsSoldPerDraw) ? "" : ticketsSoldPerDraw}
                  onChange={(e) => setTicketsSoldPerDraw(parseNumericInput(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "12px",
                    border: "1px solid #d6dee8",
                    background: "#f8fafc",
                    fontSize: "14px",
                    color: "#0f172a",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ ...cardStyle(), padding: "18px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "14px",
                  alignItems: "flex-start",
                  flexWrap: "wrap",
                }}
              >
                <div>
                  <h2
                    style={{
                      marginTop: 0,
                      marginBottom: "6px",
                      fontSize: "20px",
                      color: "#0f172a",
                    }}
                  >
                    Session controls
                  </h2>
                  <p
                    style={{
                      margin: 0,
                      color: "#475569",
                      fontSize: "14px",
                    }}
                  >
                    Results accumulate until you press Reset.
                  </p>
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: "8px",
                    flexWrap: "wrap",
                    alignItems: "center",
                  }}
                >
                  <button
                    onClick={() => buyTickets(1)}
                    disabled={loading}
                    style={primaryButtonStyle(loading)}
                  >
                    Buy 1
                  </button>
                  <button
                    onClick={() => buyTickets(10)}
                    disabled={loading}
                    style={primaryButtonStyle(loading)}
                  >
                    Buy 10
                  </button>
                  <button
                    onClick={() => buyTickets(100)}
                    disabled={loading}
                    style={primaryButtonStyle(loading)}
                  >
                    Buy 100
                  </button>

                  <input
                    type="number"
                    value={Number.isNaN(customBuyAmount) ? "" : customBuyAmount}
                    onChange={(e) => setCustomBuyAmount(parseNumericInput(e.target.value))}
                    style={{
                      padding: "10px",
                      width: "120px",
                      borderRadius: "12px",
                      border: "1px solid #d6dee8",
                      background: "#f8fafc",
                      fontSize: "14px",
                      color: "#0f172a",
                    }}
                  />

                  <button
                    onClick={() => buyTickets(customBuyAmount)}
                    disabled={loading}
                    style={primaryButtonStyle(loading)}
                  >
                    Buy custom
                  </button>

                  <button
                    onClick={handleReset}
                    disabled={loading}
                    style={dangerButtonStyle(loading)}
                  >
                    Reset
                  </button>
                </div>
              </div>

              {errorMessage && (
                <div
                  style={{
                    marginTop: "14px",
                    padding: "12px 14px",
                    borderRadius: "12px",
                    backgroundColor: "#fef2f2",
                    color: "#b91c1c",
                    border: "1px solid #fecaca",
                    whiteSpace: "pre-line",
                    fontSize: "14px",
                  }}
                >
                  {errorMessage}
                </div>
              )}
            </div>

            {/* Compact KPI cards with the most intuitive metrics for end users. */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                gap: "12px",
              }}
            >
              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  Tickets played
                </div>
                <div style={{ fontSize: "24px", fontWeight: 800, color: "#0f172a" }}>
                  {formatInteger(sessionResult.tickets_played)}
                </div>
              </div>

              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  Winning tickets
                </div>
                <div style={{ fontSize: "24px", fontWeight: 800, color: "#0f172a" }}>
                  {formatInteger(sessionResult.winning_tickets)}
                </div>
              </div>

              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  Total spent
                </div>
                <div style={{ fontSize: "24px", fontWeight: 800, color: "#0f172a" }}>
                  {formatMoney(sessionResult.total_spent)}
                </div>
              </div>

              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  Total won
                </div>
                <div style={{ fontSize: "24px", fontWeight: 800, color: "#0f172a" }}>
                  {formatMoney(sessionResult.total_won)}
                </div>
              </div>

              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  Net result
                </div>
                <div
                  style={{
                    fontSize: "24px",
                    fontWeight: 800,
                    color: netResult >= 0 ? "#166534" : "#b91c1c",
                  }}
                >
                  {formatMoney(netResult)}
                </div>
              </div>

              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  RTP
                </div>
                <div style={{ fontSize: "24px", fontWeight: 800, color: "#0f172a" }}>
                  {formatRatio(rtp)}
                </div>
              </div>

              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  Market model
                </div>
                <div
                  style={{
                    fontSize: "22px",
                    fontWeight: 800,
                    textTransform: "capitalize",
                    color: "#0f172a",
                  }}
                >
                  {marketModel}
                </div>
              </div>

              <div style={metricCardStyle()}>
                <div style={{ color: "#475569", fontSize: "13px", marginBottom: "6px" }}>
                  Your ticket
                </div>
                <div
                  style={{
                    fontSize: "15px",
                    fontWeight: 700,
                    lineHeight: 1.4,
                    color: "#0f172a",
                  }}
                >
                  {mainNumbers.join(", ")} | {euroNumbers.join(", ")}
                </div>
              </div>
            </div>

            {/* Simple horizontal bar chart inspired by dashboard-style lottery UI. */}
            <div
              style={{
                ...cardStyle(),
                padding: "18px",
              }}
            >
              <h2
                style={{
                  marginTop: 0,
                  marginBottom: "14px",
                  fontSize: "20px",
                  color: "#0f172a",
                }}
              >
                Simulation Results
              </h2>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {sortedPrizeClasses.length === 0 && (
                  <div
                    style={{
                      color: "#64748b",
                      fontSize: "14px",
                    }}
                  >
                    No results yet. Buy tickets to see the distribution.
                  </div>
                )}

                {sortedPrizeClasses.map((item) => {
                  const totalWon = safeNumber(item.actual_total_won);
                  const ticketCount = safeNumber(item.count);
                  const barWidth = `${(totalWon / maxBarValue) * 100}%`;

                  return (
                    <div
                      key={`bar-${item.key}`}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "180px minmax(0, 1fr) 110px",
                        gap: "12px",
                        alignItems: "center",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "14px",
                          color: "#334155",
                          fontWeight: 600,
                        }}
                      >
                        {item.label}
                      </div>

                      <div
                        style={{
                          position: "relative",
                          height: "14px",
                          borderRadius: "999px",
                          background: "#e9eff5",
                          overflow: "visible",
                        }}
                      >
                        <div
                          style={{
                            width: barWidth,
                            height: "100%",
                            borderRadius: "999px",
                            background: "linear-gradient(90deg, #16a34a 0%, #22c55e 100%)",
                            position: "relative",
                          }}
                        >
                          {ticketCount > 0 && (
                            <div
                              style={{
                                position: "absolute",
                                right: "-8px",
                                top: "-24px",
                                transform: "translateX(100%)",
                                fontSize: "12px",
                                fontWeight: 700,
                                color: "#0f172a",
                                whiteSpace: "nowrap",
                              }}
                            >
                              {formatInteger(ticketCount)}
                            </div>
                          )}
                        </div>
                      </div>

                      <div
                        style={{
                          textAlign: "right",
                          fontSize: "13px",
                          fontWeight: 700,
                          color: "#475569",
                        }}
                      >
                        {formatShortMoney(totalWon)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Detailed table for the same distribution shown in the chart. */}
            <div style={{ ...cardStyle(), padding: "18px" }}>
              <h2
                style={{
                  marginTop: 0,
                  marginBottom: "14px",
                  fontSize: "20px",
                  color: "#0f172a",
                }}
              >
                Prize distribution
              </h2>

              <div style={{ overflowX: "auto" }}>
                <table
                  style={{
                    borderCollapse: "collapse",
                    width: "100%",
                    minWidth: "640px",
                  }}
                >
                  <thead>
                    <tr>
                      <th
                        style={{
                          borderBottom: "1px solid #e5e7eb",
                          textAlign: "left",
                          padding: "12px 8px",
                          color: "#475569",
                          fontSize: "12px",
                          fontWeight: 800,
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                        }}
                      >
                        Category
                      </th>
                      <th
                        style={{
                          borderBottom: "1px solid #e5e7eb",
                          textAlign: "right",
                          padding: "12px 8px",
                          color: "#475569",
                          fontSize: "12px",
                          fontWeight: 800,
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                        }}
                      >
                        Count
                      </th>
                      <th
                        style={{
                          borderBottom: "1px solid #e5e7eb",
                          textAlign: "right",
                          padding: "12px 8px",
                          color: "#475569",
                          fontSize: "12px",
                          fontWeight: 800,
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                        }}
                      >
                        Avg actual payout
                      </th>
                      <th
                        style={{
                          borderBottom: "1px solid #e5e7eb",
                          textAlign: "right",
                          padding: "12px 8px",
                          color: "#475569",
                          fontSize: "12px",
                          fontWeight: 800,
                          textTransform: "uppercase",
                          letterSpacing: "0.05em",
                        }}
                      >
                        Actual total won
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedPrizeClasses.map((item) => (
                      <tr key={item.key}>
                        <td
                          style={{
                            padding: "12px 8px",
                            borderBottom: "1px solid #f1f5f9",
                            fontWeight: 600,
                            color: "#0f172a",
                          }}
                        >
                          {item.label}
                        </td>
                        <td
                          style={{
                            textAlign: "right",
                            padding: "12px 8px",
                            borderBottom: "1px solid #f1f5f9",
                            color: "#0f172a",
                          }}
                        >
                          {formatInteger(safeNumber(item.count))}
                        </td>
                        <td
                          style={{
                            textAlign: "right",
                            padding: "12px 8px",
                            borderBottom: "1px solid #f1f5f9",
                            color: "#0f172a",
                          }}
                        >
                          {formatMoney(safeNumber(item.average_actual_payout))}
                        </td>
                        <td
                          style={{
                            textAlign: "right",
                            padding: "12px 8px",
                            borderBottom: "1px solid #f1f5f9",
                            color: "#0f172a",
                          }}
                        >
                          {formatMoney(safeNumber(item.actual_total_won))}
                        </td>
                      </tr>
                    ))}
                    {sortedPrizeClasses.length === 0 && (
                      <tr>
                        <td
                          colSpan={4}
                          style={{
                            padding: "20px 8px",
                            textAlign: "center",
                            color: "#64748b",
                          }}
                        >
                          No results yet. Buy tickets to start the session.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;