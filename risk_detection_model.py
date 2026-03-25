"""
Risk Detection Model — heuristic signals for rug-pull-like conditions and liquidity stress.
Uses price + volume memory (not on-chain pool reserves).
"""
from typing import Dict, List


def detect_rug_and_liquidity_risks(
    prices: Dict[str, dict],
    market_extra: Dict[str, dict],
    prev_volume_24h: Dict[str, float],
) -> dict:
    """
    - Rug-pull proxy: sharp -24h price + thin volume (illiquid dump).
    - Liquidity drop: large drop in reported 24h volume vs previous tick.
    """
    alerts: List[dict] = []
    score = 0

    for sym, px in prices.items():
        ch = float(px.get("change_24h", 0) or 0)
        m = market_extra.get(sym, {}) or {}
        vol = float(m.get("total_volume_24h_usd", 0) or 0)
        mcap = float(m.get("market_cap_usd", 0) or 0)

        # Thin liquidity + heavy sell-off
        if ch < -30 and vol < max(5e5, mcap * 0.001 if mcap else 5e5):
            alerts.append(
                {
                    "type": "rug_pull_proxy",
                    "symbol": sym,
                    "detail": "Large 24h drop with relatively low reported volume (illiquid / risky).",
                }
            )
            score += 22

        pv = prev_volume_24h.get(sym)
        if pv and pv > 0 and vol > 0:
            ratio = vol / pv
            if ratio < 0.45:
                alerts.append(
                    {
                        "type": "liquidity_volume_drop",
                        "symbol": sym,
                        "detail": f"24h volume ~{ratio:.0%} of prior observation (liquidity stress proxy).",
                    }
                )
                score += 18
        elif pv and pv > 0 and vol <= 0:
            alerts.append(
                {
                    "type": "liquidity_volume_drop",
                    "symbol": sym,
                    "detail": "Volume collapsed vs prior tick.",
                }
            )
            score += 15

    score = min(100, score)
    return {
        "risk_score": score,
        "alerts": alerts,
        "summary": f"{len(alerts)} structural market risk signal(s)",
    }
