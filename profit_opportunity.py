"""
Profit Opportunity Engine — lightweight arbitrage / divergence hints + yield farming scan (DeFiLlama).
"""
from typing import Dict, List

import requests

from data_fetch import HTTP_HEADERS


def _pair_divergence_hints(tokens: List[str], prices: Dict[str, dict]) -> List[dict]:
    """Statistical divergence between selected pairs (not cross-DEX arb)."""
    hints: List[dict] = []
    if len(tokens) < 2:
        return hints
    changes = {t: float(prices[t].get("change_24h", 0) or 0) for t in tokens if t in prices}
    items = list(changes.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, ca = items[i]
            b, cb = items[j]
            if abs(ca - cb) > 12:
                hints.append(
                    {
                        "type": "pair_divergence",
                        "pair": [a, b],
                        "detail": f"24h move gap {ca:.1f}% vs {cb:.1f}% — possible relative-value / hedge idea.",
                    }
                )
    return hints[:8]


def _arbitrage_style_hints(prices: Dict[str, dict]) -> List[dict]:
    """
    Placeholder for true cross-venue arb (needs two prices per asset).
    Here: flag strong mean-reversion candidates after large 24h moves.
    """
    out: List[dict] = []
    for sym, p in prices.items():
        ch = float(p.get("change_24h", 0) or 0)
        if ch < -12:
            out.append(
                {
                    "type": "mean_reversion_candidate",
                    "symbol": sym,
                    "detail": "Large negative 24h move — staged buys may be considered (not financial advice).",
                }
            )
        elif ch > 15:
            out.append(
                {
                    "type": "take_profit_candidate",
                    "symbol": sym,
                    "detail": "Strong positive 24h — partial profit taking / risk reduction.",
                }
            )
    return out[:10]


def fetch_top_yield_pools(limit: int = 6) -> List[dict]:
    """DeFiLlama Yields — public pools (APY)."""
    try:
        r = requests.get("https://yields.llama.fi/pools", headers=HTTP_HEADERS, timeout=20)
        r.raise_for_status()
        raw = r.json()
        data = raw if isinstance(raw, list) else raw.get("data", [])
        ranked = sorted(
            data,
            key=lambda x: float(x.get("apy", 0) or 0),
            reverse=True,
        )
        rows = []
        for pool in ranked[:80]:
            apy = float(pool.get("apy", 0) or 0)
            if apy < 3 or apy > 500:
                continue
            rows.append(
                {
                    "project": pool.get("project", "?"),
                    "symbol": pool.get("symbol", "?"),
                    "chain": pool.get("chain", "?"),
                    "apy_pct": round(apy, 2),
                    "tvl_usd": float(pool.get("tvlUsd", 0) or 0),
                }
            )
            if len(rows) >= limit:
                break
        return rows
    except Exception:
        return []


def scan_opportunities(tokens: List[str], prices: Dict[str, dict], market_extra: Dict[str, dict]) -> dict:
    """Bundle arbitrage-style hints + yield ideas."""
    div = _pair_divergence_hints(tokens, prices)
    arb_style = _arbitrage_style_hints(prices)
    yields = fetch_top_yield_pools(6)
    return {
        "pair_divergence": div,
        "mean_reversion_and_momentum": arb_style,
        "yield_farming_ideas": yields,
        "note": "True cross-exchange arbitrage requires multiple venue prices; these are educational heuristics.",
    }
