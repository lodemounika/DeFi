"""
Multi-chain wallet activity via Etherscan-compatible explorer APIs.
Smart-contract event proxy: ERC-20 transfer count (tokentx) in recent window.
"""
import time
from typing import Dict, List

import requests

from chain_config import EXPLORER_API

_CHAIN_IDS = {"ethereum": "1", "bsc": "56", "polygon": "137"}

def _txlist(address: str, api_base: str, api_key: str, offset: int = 100, chain: str = "ethereum") -> List[dict]:
    if not address or not api_key:
        return []
    try:
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": offset,
            "sort": "desc",
            "apikey": api_key,
        }
        if "/v2/" in api_base:
            params["chainid"] = _CHAIN_IDS.get(chain, "1")
        r = requests.get(
            api_base,
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        j = r.json()
        if j.get("status") == "1" and isinstance(j.get("result"), list):
            return j["result"]
    except Exception:
        pass
    return []


def tx_frequency_last_hour_from_list(txs: List[dict]) -> int:
    now = int(time.time())
    n = 0
    for tx in txs:
        ts = tx.get("timeStamp")
        if ts is None:
            continue
        try:
            if now - int(ts) <= 3600:
                n += 1
        except (TypeError, ValueError):
            continue
    return n


def fetch_tokentx_recent(
    address: str,
    api_base: str,
    api_key: str,
    offset: int = 200,
    chain: str = "ethereum",
) -> List[dict]:
    """ERC-20 Transfer events (explorer index) — proxy for on-chain token activity."""
    if not address or not api_key:
        return []
    try:
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": 1,
            "offset": offset,
            "sort": "desc",
            "apikey": api_key,
        }
        if "/v2/" in api_base:
            params["chainid"] = _CHAIN_IDS.get(chain, "1")
        r = requests.get(
            api_base,
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        j = r.json()
        if j.get("status") == "1" and isinstance(j.get("result"), list):
            return j["result"]
    except Exception:
        pass
    return []


def token_transfer_frequency_1h(txs: List[dict]) -> int:
    return tx_frequency_last_hour_from_list(txs)


def fetch_multi_chain_wallet_intel(address: str, etherscan_key: str, bsc_key: str = "", polygon_key: str = "") -> dict:
    """
    Same EVM address works on Ethereum / BSC / Polygon; balances differ per chain.
    Uses separate API keys if provided; else repeats etherscan_key (works if your key is multi-chain).
    """
    bsc_key = bsc_key or etherscan_key
    poly_key = polygon_key or etherscan_key

    intel: Dict[str, dict] = {}
    for chain, base in EXPLORER_API.items():
        key = etherscan_key
        if chain == "bsc":
            key = bsc_key
        elif chain == "polygon":
            key = poly_key

        txs = _txlist(address, base, key, chain=chain)
        tokentx = fetch_tokentx_recent(address, base, key, chain=chain)
        intel[chain] = {
            "native_tx_last_hour": tx_frequency_last_hour_from_list(txs),
            "erc20_transfer_last_hour": token_transfer_frequency_1h(tokentx),
            "explorer_ok": bool(key),
        }

    total_native = sum(c["native_tx_last_hour"] for c in intel.values())
    total_token = sum(c["erc20_transfer_last_hour"] for c in intel.values())
    intel["_summary"] = {
        "total_native_tx_1h": total_native,
        "total_erc20_events_1h": total_token,
        "liquidity_proxy_note": "ERC-20 transfer count proxies smart-contract event activity",
    }
    return intel
