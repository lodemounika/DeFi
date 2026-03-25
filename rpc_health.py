"""JSON-RPC eth_blockNumber against EVM nodes (Ethereum, BSC, Polygon)."""
from typing import Dict, Optional

import requests

from chain_config import DEFAULT_RPC


def _block_number(rpc_url: str) -> Optional[int]:
    try:
        r = requests.post(
            rpc_url,
            json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        if "result" not in data:
            return None
        return int(data["result"], 16)
    except Exception:
        return None


def ping_all_nodes() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for name, url in DEFAULT_RPC.items():
        bn = _block_number(url)
        out[name] = {
            "rpc_url": url,
            "block_number": bn,
            "ok": bn is not None,
        }
    return out
