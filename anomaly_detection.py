"""
Anomaly Detection — flags unusually large native transfers and large ERC-20 moves (whale proxy).
"""
from typing import Dict, List


def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def detect_whale_anomalies(
    transactions: List[dict],
    tokentx: List[dict],
    native_eth_threshold: float = 5.0,
    token_usd_proxy_threshold: float = 250_000.0,
) -> dict:
    """
    Whale heuristics:
    - Native: ETH value >= threshold
    - ERC-20: raw amount * $1 rough proxy if decimals missing; prefer large raw values
    """
    whale_events: List[dict] = []

    for tx in (transactions or [])[:80]:
        wei = int(tx.get("value") or 0)
        eth = wei / 1e18
        if eth >= native_eth_threshold:
            whale_events.append(
                {
                    "kind": "native_whale",
                    "hash": tx.get("hash"),
                    "value_eth": round(eth, 4),
                    "from": tx.get("from"),
                    "to": tx.get("to"),
                }
            )

    for tt in (tokentx or [])[:120]:
        try:
            decimals = int(tt.get("tokenDecimal", 18))
        except (TypeError, ValueError):
            decimals = 18
        raw = _safe_float(tt.get("value"))
        qty = raw / (10**decimals) if raw else 0.0
        sym = (tt.get("tokenSymbol") or "?").upper()
        # USD proxy: stablecoins ~1:1; else skip USD gate, use huge qty
        if sym in ("USDT", "USDC", "DAI", "BUSD") and qty >= token_usd_proxy_threshold / 1.0:
            whale_events.append(
                {
                    "kind": "stablecoin_whale",
                    "hash": tt.get("hash"),
                    "symbol": sym,
                    "qty": qty,
                    "from": tt.get("from"),
                    "to": tt.get("to"),
                }
            )
        elif qty >= 1e9 and sym in ("SHIB", "PEPE"):
            whale_events.append(
                {
                    "kind": "meme_token_whale",
                    "hash": tt.get("hash"),
                    "symbol": sym,
                    "qty": qty,
                }
            )

    return {
        "whale_events": whale_events[:25],
        "whale_count": len(whale_events),
        "anomaly_score": min(100, len(whale_events) * 8),
        "summary": f"{len(whale_events)} unusual large transfer(s) detected",
    }
