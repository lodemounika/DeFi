"""
Market data: CoinGecko (volume, liquidity proxy) + DeFiLlama (Uniswap / Aave protocol TVL).
"""
from typing import Dict, List

import requests

from data_fetch import COINGECKO_IDS, HTTP_HEADERS


def fetch_coingecko_markets_extra(symbols: List[str]) -> Dict[str, dict]:
    """Per-asset: total_volume (24h), price change — for liquidity/volume risk context."""
    ids = [COINGECKO_IDS[s] for s in symbols if s in COINGECKO_IDS]
    if not ids:
        return {}
    out: Dict[str, dict] = {}
    chunk = 40
    for i in range(0, len(ids), chunk):
        part = ids[i : i + chunk]
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "ids": ",".join(part),
                    "order": "market_cap_desc",
                    "per_page": len(part),
                    "page": 1,
                    "sparkline": "false",
                },
                headers=HTTP_HEADERS,
                timeout=20,
            )
            r.raise_for_status()
            rows = r.json()
            for row in rows:
                cid = row.get("id")
                sym = next((s for s, i in COINGECKO_IDS.items() if i == cid), None)
                if not sym:
                    continue
                out[sym] = {
                    "total_volume_24h_usd": float(row.get("total_volume") or 0),
                    "market_cap_usd": float(row.get("market_cap") or 0),
                    "price_change_24h_pct": float(row.get("price_change_percentage_24h") or 0),
                }
        except Exception:
            continue
    return out


def fetch_defillama_protocol(slug: str) -> dict:
    """TVL for a protocol via DeFiLlama (numeric endpoint is most reliable)."""
    # Primary: returns a single TVL number as plain JSON
    try:
        r = requests.get(f"https://api.llama.fi/tvl/{slug}", headers=HTTP_HEADERS, timeout=20)
        r.raise_for_status()
        tvl = float(r.text.strip())
        if tvl > 0:
            return {"name": slug.title(), "tvl": tvl, "slug": slug, "error": False}
    except Exception:
        pass
    # Fallback: full protocol object
    try:
        r = requests.get(f"https://api.llama.fi/protocol/{slug}", headers=HTTP_HEADERS, timeout=20)
        r.raise_for_status()
        d = r.json()
        return {
            "name": d.get("name", slug),
            "tvl": float(d.get("tvl") or 0),
            "slug": d.get("slug", slug),
            "error": False,
        }
    except Exception:
        return {"name": slug, "tvl": 0.0, "slug": slug, "error": True}


def fetch_defi_pulse() -> dict:
    """DEX / lending pulse: Uniswap + Aave headline TVL from DeFiLlama."""
    return {
        "uniswap": fetch_defillama_protocol("uniswap"),
        "aave": fetch_defillama_protocol("aave"),
    }
