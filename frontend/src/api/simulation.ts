/**
 * Thin frontend API wrapper.
 *
 * All browser requests to the backend are routed through this module so the
 * application has a single place to read the production API URL and parse
 * backend validation errors.
 */

import type { SimulationRequest, SimulationResponse } from "../types/simulation";

const API_URL = import.meta.env.VITE_API_URL;

export async function runSimulation(
  payload: SimulationRequest
): Promise<SimulationResponse> {
  const response = await fetch(`${API_URL}/simulate`, {
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
      // ignore JSON parsing errors
    }

    throw new Error(message);
  }

  return response.json();
}