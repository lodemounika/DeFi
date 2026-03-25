import asyncio
import random
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel


class Alert(BaseModel):
    timestamp: str
    risk_score: int
    risk_level: str
    reason: str
    recommendation: str
    on_chain_txn: str


class Snapshot(BaseModel):
    token_price: float
    volume_24h: float
    liquidity: float
    suspicious_wallet_score: float
    risk_score: int
    risk_level: str
    recommendation: str
    updated_at: str


app = FastAPI(title="DeFi Guardian API", version="0.1.0")

state = {
    "snapshot": Snapshot(
        token_price=0.28,
        volume_24h=1200000.0,
        liquidity=4800000.0,
        suspicious_wallet_score=0.11,
        risk_score=23,
        risk_level="low",
        recommendation="monitor",
        updated_at=datetime.now(timezone.utc).isoformat(),
    ),
    "alerts": [],
}


def classify_risk(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def recommendation_for(level: str) -> str:
    if level == "high":
        return "sell"
    if level == "medium":
        return "hold"
    return "monitor"


def simulate_market_tick() -> None:
    previous = state["snapshot"]
    token_price = max(0.01, round(previous.token_price + random.uniform(-0.04, 0.04), 4))
    volume_24h = max(1000.0, previous.volume_24h * random.uniform(0.93, 1.08))
    liquidity = max(10000.0, previous.liquidity * random.uniform(0.95, 1.04))
    suspicious_wallet_score = min(1.0, max(0.0, previous.suspicious_wallet_score + random.uniform(-0.05, 0.08)))

    price_stress = min(35, abs(token_price - previous.token_price) * 800)
    volume_stress = min(30, abs(volume_24h - previous.volume_24h) / max(1.0, previous.volume_24h) * 320)
    liquidity_stress = min(20, abs(liquidity - previous.liquidity) / max(1.0, previous.liquidity) * 240)
    wallet_stress = suspicious_wallet_score * 25
    risk_score = int(min(100, price_stress + volume_stress + liquidity_stress + wallet_stress))

    risk_level = classify_risk(risk_score)
    recommendation = recommendation_for(risk_level)
    updated_at = datetime.now(timezone.utc).isoformat()

    state["snapshot"] = Snapshot(
        token_price=token_price,
        volume_24h=round(volume_24h, 2),
        liquidity=round(liquidity, 2),
        suspicious_wallet_score=round(suspicious_wallet_score, 3),
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation=recommendation,
        updated_at=updated_at,
    )

    if risk_level in {"medium", "high"}:
        alert = Alert(
            timestamp=updated_at,
            risk_score=risk_score,
            risk_level=risk_level,
            reason="Autonomous agent detected volatility and flow anomalies.",
            recommendation=recommendation,
            on_chain_txn=f"ALGO_TX_{random.randint(100000, 999999)}",
        )
        state["alerts"].insert(0, alert)
        state["alerts"] = state["alerts"][:25]


async def agent_loop() -> None:
    while True:
        simulate_market_tick()
        await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(agent_loop())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "defi-guardian-agent"}


@app.get("/api/snapshot", response_model=Snapshot)
def get_snapshot() -> Snapshot:
    return state["snapshot"]


@app.get("/api/alerts", response_model=List[Alert])
def get_alerts() -> List[Alert]:
    return state["alerts"]
