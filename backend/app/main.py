"""FastAPI entry point used both locally and in production.

The application exposes a simple health-check endpoint and one simulation
endpoint consumed by the frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import SimulationRequest, SimulationResponse
from app.simulator_service import simulate_lottery

app = FastAPI(title="Eurojackpot Simulation API")

# CORS allows the browser-based frontend to call this backend from local Vite
# during development and from the deployed Vercel domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://eurojackpot-simulator.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """Return a simple health-check message."""
    return {"message": "Eurojackpot backend is running"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(payload: SimulationRequest) -> SimulationResponse:
    """Run one simulation batch using the request payload."""
    return simulate_lottery(payload)
