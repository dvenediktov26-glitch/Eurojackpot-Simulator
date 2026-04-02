from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import SimulationRequest, SimulationResponse
from app.simulator_service import simulate_lottery

app = FastAPI(title="Eurojackpot Simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Eurojackpot backend is running"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(payload: SimulationRequest):
    return simulate_lottery(payload)