# DeFi Guardian: Agentic AI Monitoring System using Algorand Blockchain

Fully working Streamlit project that demonstrates:
- **Observe**: CoinGecko prices + Etherscan wallet transactions
- **Reason**: Risk scoring engine with explainable output
- **Act**: Real-time alerts and Algorand logging (real or simulated)
- **Learn/Memory**: Stores past risk and detects trend behavior

## Project Structure

- `app.py` - Streamlit UI and autonomous loop
- `data_fetch.py` - CoinGecko and Etherscan integration
- `transaction_parser.py` - **Processing layer**: decode `txlist` (method IDs, native vs contract calls)
- `event_listener.py` - **Processing layer**: classify ERC-20 flows (DEX / lending proxies)
- `data_normalizer.py` - **Processing layer**: unified schema for UI + risk hints
- `risk_detection_model.py` - Rug-pull / liquidity stress heuristics (volume memory + price)
- `anomaly_detection.py` - Whale-style large transfer detection
- `profit_opportunity.py` - Yield scan (DeFiLlama) + pair divergence / momentum hints
- `prediction_model.py` - **ML**: NumPy OLS linear trend on recent prices per asset (no sklearn)
- `risk_engine.py` - Risk score logic and explanations
- `agent.py` - Agent loop (observe, reason, act, memory)
- `algorand_logger.py` - Algorand logging (with simulation fallback)
- `chain_config.py`, `evm_intel.py`, `rpc_health.py`, `defi_market_intel.py` - multi-chain & DeFi data
- `requirements.txt` - Python dependencies

## Setup

```bash
cd "c:\Users\Tejaswini\Downloads\defi-guardian"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Optional Environment Variables

For better real-data quality:

```powershell
$env:ETHERSCAN_API_KEY="your_etherscan_key"
```

For real Algorand logging (otherwise simulated by default):

```powershell
$env:SIMULATE_ALGORAND="false"
$env:ALGOD_ADDRESS="https://testnet-api.algonode.cloud"
$env:ALGOD_TOKEN=""
$env:ALGORAND_MNEMONIC="your 25 word mnemonic"
```

`ALGOD_TOKEN` can stay empty for public Algonode endpoints. Fund the account from the [Algorand testnet dispenser](https://bank.testnet.algorand.network/) so transactions succeed.

## Run

```bash
python -m streamlit run app.py
```

## Features Implemented

- **Multi-crypto monitoring**: ~45 major assets via CoinGecko (BTC, ETH, SOL, ADA, …); select any combination in the sidebar
- Multi-asset portfolio: selected cryptos + **GOLD**, **SILVER**, **CASH**
- Auto wallet fetch for **ETH** and **BTC** only when their units are set to `0` (Etherscan). Other coins use the quantity you enter.
- Risk score (0-100) using:
  - crypto exposure ratio
  - wallet activity (tx/hour)
  - scenario price-drop stress
- Risk levels:
  - `0-30` -> `LOW`
  - `31-70` -> `MEDIUM`
  - `71-100` -> `HIGH`
- Decision engine:
  - `HIGH` -> `SELL`
  - `MEDIUM` -> `MONITOR`
  - `LOW` -> `HOLD`
- Explainable rule-based AI insight
- Trading signal engine + liquidity risk + diversification suggestions
- Lending analysis panel (5% estimate)
- Color-coded alert history (green/yellow/red semantics)
- Full graph dashboard:
  - Risk score trend
  - Token and metal trend
  - Transaction trend
  - Portfolio value trend
  - Portfolio composition chart
  - Plotly pie/line/bar visualizations
- On-chain alert logging (or simulation) with local audit file:
  - `algorand_alert_log.jsonl`

## Notes

- If an API call fails, the app uses synthetic fallback data so demos still work.
- Auto holdings require `ETHERSCAN_API_KEY`; without it, holdings default to `0`.
- BTC holding is derived from WBTC balance on Ethereum wallet.
- Invalid Algorand mnemonic or network issues do not crash the app ("Blockchain not connected").
- Keep Algorand simulation mode enabled for first run unless your testnet wallet is funded.
