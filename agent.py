import os
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List

from algorand_logger import AlgorandLogger
from chain_config import EXPLORER_API
from data_fetch import (
    fetch_prices,
    fetch_wallet_holdings,
    fetch_wallet_transactions,
    simulate_metal_prices,
    tx_frequency_last_hour,
)
from anomaly_detection import detect_whale_anomalies
from data_normalizer import empty_processing_bundle, normalize_processing_output
from defi_market_intel import fetch_coingecko_markets_extra, fetch_defi_pulse
from evm_intel import fetch_tokentx_recent
from prediction_model import predict_price_trends
from profit_opportunity import scan_opportunities
from risk_detection_model import detect_rug_and_liquidity_risks
from evm_intel import fetch_multi_chain_wallet_intel
from rpc_health import ping_all_nodes
from risk_engine import (
    build_explanation,
    calculate_risk_score,
    classify_risk,
    decision_for_risk,
    diversification_suggestion,
    liquidity_risk_flag,
    risk_flags,
    trading_signal,
)


class DeFiGuardianAgent:
    def __init__(self, logger: AlgorandLogger, etherscan_api_key: str) -> None:
        self.logger = logger
        self.etherscan_api_key = etherscan_api_key
        self.risk_history: Deque[dict] = deque(maxlen=100)
        self.alert_history: Deque[dict] = deque(maxlen=50)
        self.observation_history: Deque[dict] = deque(maxlen=200)
        self.portfolio_history: Deque[dict] = deque(maxlen=200)
        self.asset_price_history: Deque[dict] = deque(maxlen=200)
        self._prev_market_volume: Dict[str, float] = {}

    def observe(
        self,
        wallet_address: str,
        tokens: List[str],
        scenario_drop_pct: float,
        health_factor: float,
    ) -> dict:
        prices = fetch_prices(tokens)
        simulated_crypto = {}
        for token, info in prices.items():
            live_price = float(info.get("price", 0.0))
            shocked_price = live_price * max(0.0, 1 - (scenario_drop_pct / 100))
            simulated_crypto[token] = {
                "live_price": live_price,
                "simulated_price": shocked_price,
                "change_24h": float(info.get("change_24h", 0.0)),
            }
        transactions = fetch_wallet_transactions(wallet_address, self.etherscan_api_key)
        holdings = fetch_wallet_holdings(wallet_address, self.etherscan_api_key, tokens)
        tx_freq = tx_frequency_last_hour(transactions)

        tokentx_eth: List[dict] = []
        try:
            tokentx_eth = fetch_tokentx_recent(
                wallet_address,
                EXPLORER_API["ethereum"],
                self.etherscan_api_key,
            )
            processing_layer = normalize_processing_output(transactions, tokentx_eth)
        except Exception:
            processing_layer = empty_processing_bundle()
            tokentx_eth = []

        multi_chain = fetch_multi_chain_wallet_intel(
            wallet_address,
            self.etherscan_api_key,
            os.getenv("BSCSCAN_API_KEY", "") or self.etherscan_api_key,
            os.getenv("POLYGONSCAN_API_KEY", "") or self.etherscan_api_key,
        )
        market_extra = fetch_coingecko_markets_extra(tokens)
        defi_pulse = fetch_defi_pulse()
        rpc_nodes = ping_all_nodes()
        defi_tvl_sum = float(defi_pulse.get("uniswap", {}).get("tvl") or 0) + float(
            defi_pulse.get("aave", {}).get("tvl") or 0
        )

        hist_for_ml = list(self.asset_price_history)
        predictions = predict_price_trends(hist_for_ml, tokens)
        rug_det = detect_rug_and_liquidity_risks(simulated_crypto, market_extra, self._prev_market_volume)
        for sym in tokens:
            if sym in market_extra:
                self._prev_market_volume[sym] = float(market_extra[sym].get("total_volume_24h_usd", 0) or 0)
        anomalies = detect_whale_anomalies(transactions, tokentx_eth)
        profit_opp = scan_opportunities(tokens, simulated_crypto, market_extra)
        advanced_intel = {
            "risk_detection_model": rug_det,
            "anomaly_detection": anomalies,
            "profit_opportunity": profit_opp,
            "ml_predictions": predictions,
        }

        previous_metals = self.asset_price_history[-1] if self.asset_price_history else {}
        metal_prices = simulate_metal_prices(previous_metals)
        observation = {
            "wallet": wallet_address,
            "tokens": tokens,
            "prices": simulated_crypto,
            "metal_prices": metal_prices,
            "holdings": holdings,
            "transactions": transactions,
            "processing_layer": processing_layer,
            "tx_frequency": tx_freq,
            "multi_chain": multi_chain,
            "market_extra": market_extra,
            "defi_pulse": defi_pulse,
            "rpc_nodes": rpc_nodes,
            "health_factor": float(health_factor),
            "defi_tvl_sum": defi_tvl_sum,
            "scenario_drop_pct": scenario_drop_pct,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "advanced_intel": advanced_intel,
        }
        price_row: Dict[str, float] = {
            "timestamp": observation["observed_at"],
            "GOLD": metal_prices["GOLD"],
            "SILVER": metal_prices["SILVER"],
        }
        for t in tokens:
            price_row[t] = float(simulated_crypto.get(t, {}).get("simulated_price", 0.0))
        self.asset_price_history.append(price_row)
        self.observation_history.append(observation)
        return observation

    def _quantity_for_crypto(self, symbol: str, holdings: Dict[str, float], allocations: Dict[str, float]) -> float:
        manual = float(allocations.get(symbol, 0.0) or 0.0)
        if symbol in ("ETH", "BTC") and manual == 0.0:
            return float(holdings.get(symbol, 0.0) or 0.0)
        return manual

    def _compute_portfolio(self, observation: Dict, allocations: Dict[str, float]) -> dict:
        prices = observation["prices"]
        metal_prices = observation["metal_prices"]
        holdings = observation["holdings"]
        tokens = observation["tokens"]

        token_values: Dict[str, Dict] = {}
        crypto_value = 0.0
        for sym in tokens:
            qty = self._quantity_for_crypto(sym, holdings, allocations)
            px = float(prices.get(sym, {}).get("simulated_price", 0.0))
            val = round(qty * px, 2)
            token_values[sym] = {"quantity": qty, "price": px, "value_usd": val}
            crypto_value += val

        gold_units = float(allocations.get("GOLD", 0.0) or 0.0)
        silver_units = float(allocations.get("SILVER", 0.0) or 0.0)
        cash = float(allocations.get("CASH", 0.0) or 0.0)

        token_values["GOLD"] = {
            "quantity": gold_units,
            "price": metal_prices["GOLD"],
            "value_usd": round(gold_units * metal_prices["GOLD"], 2),
        }
        token_values["SILVER"] = {
            "quantity": silver_units,
            "price": metal_prices["SILVER"],
            "value_usd": round(silver_units * metal_prices["SILVER"], 2),
        }
        token_values["CASH"] = {"quantity": cash, "price": 1.0, "value_usd": round(cash, 2)}

        non_crypto_value = (
            token_values["GOLD"]["value_usd"] + token_values["SILVER"]["value_usd"] + token_values["CASH"]["value_usd"]
        )
        total_value = crypto_value + non_crypto_value
        crypto_ratio = (crypto_value / total_value) * 100 if total_value > 0 else 0.0

        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_value_usd": round(total_value, 2),
            "crypto_value_usd": round(crypto_value, 2),
            "crypto_ratio_pct": round(crypto_ratio, 2),
            "token_values": token_values,
        }
        self.portfolio_history.append(snapshot)
        return snapshot

    def reason(self, observation: dict, portfolio: dict) -> dict:
        tokens = observation["tokens"]
        avg_change = 0.0
        if tokens:
            changes = []
            for t in tokens:
                if t in observation["prices"]:
                    changes.append(float(observation["prices"][t].get("change_24h", 0.0)))
            avg_change = sum(changes) / len(changes) if changes else 0.0

        summary = observation.get("multi_chain", {}).get("_summary", {})
        multi_native = int(summary.get("total_native_tx_1h", 0) or 0)
        erc20 = int(summary.get("total_erc20_events_1h", 0) or 0)

        market_extra = observation.get("market_extra") or {}
        mc_changes: List[float] = []
        for t in tokens:
            if t in market_extra:
                mc_changes.append(float(market_extra[t].get("price_change_24h_pct", 0.0)))
        if mc_changes:
            market_avg = sum(mc_changes) / len(mc_changes)
        else:
            market_avg = avg_change

        hf = float(observation.get("health_factor", 1.5) or 1.5)

        score = calculate_risk_score(
            crypto_ratio_pct=portfolio["crypto_ratio_pct"],
            tx_frequency_hour=observation["tx_frequency"],
            scenario_drop_pct=observation["scenario_drop_pct"],
            multi_chain_native_1h=multi_native,
            erc20_events_1h=erc20,
            market_avg_change_24h=market_avg,
            health_factor=hf,
            defi_tvl_sum=float(observation.get("defi_tvl_sum", 0.0) or 0.0),
        )
        level = classify_risk(score)
        trend_direction = self._market_trend()
        fl = risk_flags(erc20, multi_native, market_avg, hf)
        explanation = build_explanation(
            risk_level=level,
            crypto_ratio_pct=portfolio["crypto_ratio_pct"],
            tx_frequency_hour=observation["tx_frequency"],
            trend_direction=trend_direction,
            flags=fl,
        )
        signal, signal_text = trading_signal(avg_change, observation["scenario_drop_pct"])

        decision = {
            "risk_score": score,
            "risk_level": level,
            "recommendation": decision_for_risk(level),
            "explanation": explanation,
            "liquidity_risk": liquidity_risk_flag(portfolio["crypto_ratio_pct"]),
            "trading_signal": signal,
            "trading_signal_text": signal_text,
            "diversification": diversification_suggestion(portfolio["crypto_ratio_pct"]),
            "tx_frequency": observation["tx_frequency"],
            "avg_crypto_change_24h": round(avg_change, 2),
            "risk_flags": fl,
            "multi_chain_native_1h": multi_native,
            "erc20_events_1h": erc20,
            "observed_at": observation["observed_at"],
        }
        return decision

    def act(self, decision: dict) -> dict:
        self.risk_history.append(
            {
                "timestamp": decision["observed_at"],
                "risk_score": decision["risk_score"],
                "risk_level": decision["risk_level"],
            }
        )

        should_alert = decision["risk_level"] in {"MEDIUM", "HIGH"}
        alert = None
        if should_alert:
            payload = {
                "risk_level": decision["risk_level"],
                "timestamp": decision["observed_at"],
                "reason": decision["explanation"],
                "recommendation": decision["recommendation"],
            }
            tx_id = self.logger.log_alert(payload)
            alert = {
                "timestamp": decision["observed_at"],
                "risk_score": decision["risk_score"],
                "risk_level": decision["risk_level"],
                "reason": decision["explanation"],
                "algorand_tx_id": tx_id,
            }
            self.alert_history.appendleft(alert)
        return {"alert": alert, "agent_action": decision["recommendation"]}

    def step(
        self,
        wallet_address: str,
        tokens: List[str],
        allocations: Dict[str, float],
        scenario_drop_pct: float,
        health_factor: float = 1.5,
    ) -> dict:
        observation = self.observe(wallet_address, tokens, scenario_drop_pct, health_factor)
        portfolio = self._compute_portfolio(observation, allocations)
        decision = self.reason(observation, portfolio)
        action = self.act(decision)
        return {
            "observation": observation,
            "decision": decision,
            "portfolio": portfolio,
            "action": action,
            "risk_history": list(self.risk_history),
            "alert_history": list(self.alert_history),
            "observation_history": list(self.observation_history),
            "portfolio_history": list(self.portfolio_history),
            "asset_price_history": list(self.asset_price_history),
        }

    def _market_trend(self) -> str:
        if len(self.asset_price_history) < 3:
            return "stable"
        recent = list(self.asset_price_history)[-3:]
        keys = [k for k in recent[-1] if k not in ("timestamp", "GOLD", "SILVER")]
        if not keys:
            return "stable"
        latest = sum(recent[-1].get(k, 0.0) for k in keys)
        earliest = sum(recent[0].get(k, 0.0) for k in keys)
        if latest > earliest:
            return "upward"
        if latest < earliest:
            return "downward"
        return "stable"
