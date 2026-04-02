import type { SimulationRequest, SimulationResponse } from "../types/simulation";

export async function runSimulation(
  payload: SimulationRequest
): Promise<SimulationResponse> {
  const response = await fetch("http://127.0.0.1:8010/simulate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = "Simulation failed";

    try {
      const errorData = await response.json();

      if (errorData?.detail) {
        if (typeof errorData.detail === "string") {
          message = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          message = errorData.detail
            .map((item: { loc?: unknown[]; msg?: string }) => {
              const path = Array.isArray(item.loc) ? item.loc.join(".") : "field";
              return `${path}: ${item.msg ?? "invalid value"}`;
            })
            .join("\n");
        }
      }
    } catch {
      // ignore JSON parsing errors and keep default message
    }

    throw new Error(message);
  }

  return response.json();
}