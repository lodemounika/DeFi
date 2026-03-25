"""
Transaction Parser — decodes raw explorer `txlist` rows into structured activity.
Uses method id (first 4 bytes) + value heuristics (no full ABI decode).
"""
from typing import Dict, List

# Common function selectors (first 4 bytes of keccak256)
_METHOD_HINTS = {
    "0xa9059cbb": "erc20_transfer",
    "0x095ea7b3": "erc20_approve",
    "0x23b872dd": "erc20_transferFrom",
    "0x38ed1739": "uniswap_v2_swapExactTokensForTokens",
    "0x8803dbee": "uniswap_v2_swapTokensForExactTokens",
    "0x7ff36ab1": "uniswap_v2_swapExactETHForTokens",
    "0x18cbafe5": "uniswap_v2_swapExactETHForTokens_alt",
    "0x414bf389": "uniswap_v3_exactInputSingle",
    "0xc04b8d59": "uniswap_v3_exactInput",
    "0x3d18b912": "aave_repay",
    "0x617ba037": "aave_supply",
    "0x69328dec": "aave_withdraw",
    "0xa415bcad": "aave_borrow",
    "0x4a25d94a": "aave_liquidationCall",
    "0xa0712d68": "staking_stake",
    "0x3ccfd60b": "staking_withdraw",
}


def _method_id(tx_input: str) -> str:
    s = (tx_input or "0x").lower().strip()
    if len(s) < 10:
        return "0x"
    return s[:10]


def parse_transaction(tx: dict) -> dict:
    """Single tx from Etherscan txlist → structured record."""
    # Fallback rows (used when explorer fetch fails) often only include timeStamp.
    if set(tx.keys()) <= {"timeStamp"}:
        return {
            "hash": None,
            "block": None,
            "from": None,
            "to": None,
            "value_eth": 0.0,
            "method_id": "0x",
            "category": "fallback_sample",
            "action": "simulated_fallback",
            "is_error": False,
        }

    tx_input = tx.get("input") or "0x"
    mid = _method_id(tx_input)
    value_wei = int(tx.get("value") or 0)
    value_eth = value_wei / 1e18

    hint = _METHOD_HINTS.get(mid, None)
    if value_wei > 0 and (not tx_input or tx_input == "0x"):
        category = "native_transfer"
        action = "eth_move"
    elif hint:
        category = "defi_or_token"
        action = hint
    elif len(tx_input) > 10:
        category = "contract_call"
        action = "unknown_contract_call"
    else:
        category = "empty_input"
        action = "noop"

    return {
        "hash": tx.get("hash"),
        "block": tx.get("blockNumber"),
        "from": tx.get("from"),
        "to": tx.get("to"),
        "value_eth": round(value_eth, 8),
        "method_id": mid,
        "category": category,
        "action": action,
        "is_error": tx.get("isError") == "1",
    }


def parse_transaction_batch(txlist: List[dict], limit: int = 80) -> List[dict]:
    """Decode a batch of transactions (most recent first)."""
    out: List[dict] = []
    for tx in (txlist or [])[:limit]:
        try:
            out.append(parse_transaction(tx))
        except Exception:
            continue
    return out


def summarize_parsed(parsed: List[dict]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for p in parsed:
        key = p.get("action") or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts
