"""
Public RPC endpoints (read-only) for Ethereum, BSC, Polygon.
Override with env: ETH_RPC_URL, BSC_RPC_URL, POLYGON_RPC_URL
"""
import os

DEFAULT_RPC = {
    "ethereum": os.getenv("ETH_RPC_URL", "https://ethereum.publicnode.com"),
    "bsc": os.getenv("BSC_RPC_URL", "https://bsc.publicnode.com"),
    "polygon": os.getenv("POLYGON_RPC_URL", "https://polygon-bor.publicnode.com"),
}

# Etherscan-compatible HTTP APIs (same key often works across Etherscan family)
EXPLORER_API = {
    "ethereum": "https://api.etherscan.io/v2/api",
    "bsc": "https://api.bscscan.com/api",
    "polygon": "https://api.polygonscan.com/api",
}
