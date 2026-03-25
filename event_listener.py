"""
Event Listener — maps ERC-20 `tokentx` rows + known contracts to event categories.
(Streaming listener is approximated via explorer polling in this app.)
"""
from typing import Dict, List

# Known router / protocol addresses (lowercase) — extend as needed
UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
AAVE_POOL_V3_ETH = "0x87870bca3f3de633730be8c930f44bfee2972fc2"  # mainnet pool

_KNOWN = {
    UNISWAP_V2_ROUTER: "uniswap_v2_router",
    UNISWAP_V3_ROUTER: "uniswap_v3_router",
    AAVE_POOL_V3_ETH: "aave_v3_pool",
}


def _lower(addr: str) -> str:
    return (addr or "").lower()


def classify_token_transfer(row: dict) -> str:
    """Classify a single tokentx row into a high-level event type."""
    to_c = _lower(row.get("to", ""))
    from_c = _lower(row.get("from", ""))
    for addr, label in _KNOWN.items():
        if to_c == addr or from_c == addr:
            if "uniswap" in label:
                return "dex_swap_flow"
            if "aave" in label:
                return "lending_flow"
    return "erc20_transfer"


def extract_events_from_token_transfers(tokentx: List[dict], limit: int = 120) -> List[dict]:
    """Turn indexed token transfers into structured events."""
    events: List[dict] = []
    for row in (tokentx or [])[:limit]:
        try:
            et = classify_token_transfer(row)
            events.append(
                {
                    "event_type": et,
                    "token_symbol": row.get("tokenSymbol", "?"),
                    "token_contract": row.get("contractAddress"),
                    "from": row.get("from"),
                    "to": row.get("to"),
                    "value_raw": row.get("value"),
                    "tx_hash": row.get("hash"),
                    "block": row.get("blockNumber"),
                }
            )
        except Exception:
            continue
    return events


def summarize_events(events: List[dict]) -> Dict[str, int]:
    c: Dict[str, int] = {}
    for e in events:
        t = e.get("event_type", "unknown")
        c[t] = c.get(t, 0) + 1
    return c


def flag_liquidation_risk_proxy(events: List[dict]) -> Dict[str, bool]:
    """Heuristic flags (true on-chain liquidation needs position oracles)."""
    dex_hits = sum(1 for e in events if e.get("event_type") == "dex_swap_flow")
    lend_hits = sum(1 for e in events if e.get("event_type") == "lending_flow")
    return {
        "high_dex_activity": dex_hits >= 5,
        "lending_touch": lend_hits >= 1,
    }
