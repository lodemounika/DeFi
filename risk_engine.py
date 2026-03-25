from typing import Dict, Tuple


def classify_risk(score: int) -> str:
    if score <= 30:
        return "LOW"
    if score <= 70:
        return "MEDIUM"
    return "HIGH"


def decision_for_risk(risk_level: str) -> str:
    if risk_level == "HIGH":
        return "SELL"
    if risk_level == "MEDIUM":
        return "MONITOR"
    return "HOLD"


def calculate_risk_score(
    crypto_ratio_pct: float,
    tx_frequency_hour: int,
    scenario_drop_pct: float,
    multi_chain_native_1h: int = 0,
    erc20_events_1h: int = 0,
    market_avg_change_24h: float = 0.0,
    health_factor: float = 1.5,
    defi_tvl_sum: float = 0.0,
) -> int:
    """
    Composite 0–100: portfolio exposure, multi-chain activity, event proxy,
    market stress, simulated liquidation (health factor), optional DeFi TVL context.
    """
    exposure_component = min(55.0, max(0.0, crypto_ratio_pct) * 0.75)

    # Activity: native txs across ETH/BSC/Polygon + ERC-20 event proxy (abnormal activity)
    activity_base = max(tx_frequency_hour, multi_chain_native_1h)
    activity_component = min(18.0, max(0, activity_base - 1) * 1.4)
    event_component = min(12.0, max(0, erc20_events_1h - 5) * 0.25)

    stress_component = min(10.0, max(0.0, scenario_drop_pct) * 0.55)

    # Market stress: broad negative 24h moves
    market_component = min(10.0, max(0.0, -market_avg_change_24h) * 0.35)

    # Liquidation proxy (Aave-style health factor < 1.0 at risk)
    liq_component = 0.0
    if health_factor < 1.05:
        liq_component = 18.0
    elif health_factor < 1.15:
        liq_component = 10.0
    elif health_factor < 1.3:
        liq_component = 4.0

    # Very small TVL context (optional dampening when majors are deep)
    tvl_dampen = 0.0
    if defi_tvl_sum > 1e9:
        tvl_dampen = -2.0

    raw = (
        exposure_component
        + activity_component
        + event_component
        + stress_component
        + market_component
        + liq_component
        + tvl_dampen
    )
    return int(min(100, max(0, round(raw))))


def build_explanation(
    risk_level: str,
    crypto_ratio_pct: float,
    tx_frequency_hour: int,
    trend_direction: str,
    flags: Dict[str, str],
) -> str:
    base = (
        f"{risk_level} risk due to {crypto_ratio_pct:.1f}% crypto exposure, "
        f"{tx_frequency_hour} ETH txs/h (reference), {trend_direction} trend."
    )
    extra = []
    if flags.get("abnormal_activity") == "yes":
        extra.append("abnormal multi-chain / token event activity")
    if flags.get("liquidation_watch") == "yes":
        extra.append("lending health factor in danger zone")
    if flags.get("market_stress") == "yes":
        extra.append("broad market drawdown stress")
    if extra:
        base += " Flags: " + "; ".join(extra) + "."
    return base


def trading_signal(avg_crypto_change_24h: float, scenario_drop_pct: float) -> Tuple[str, str]:
    effective_change = avg_crypto_change_24h - scenario_drop_pct
    if effective_change <= -5:
        return "BUY_OPPORTUNITY", "Crypto dropped sharply; staged accumulation can be considered."
    if effective_change >= 4:
        return "TAKE_PROFIT", "Prices moved up strongly; partial profit booking may reduce risk."
    return "NEUTRAL", "No strong trading edge detected."


def diversification_suggestion(crypto_ratio_pct: float) -> str:
    if crypto_ratio_pct > 70:
        return "Diversify from crypto into gold/silver/cash to reduce concentration risk."
    if crypto_ratio_pct > 45:
        return "Moderate exposure. Consider balancing with defensive assets."
    return "Portfolio is relatively balanced; maintain periodic rebalancing."


def liquidity_risk_flag(crypto_ratio_pct: float) -> str:
    return "OVEREXPOSED" if crypto_ratio_pct >= 65 else "MANAGEABLE"


def risk_flags(
    erc20_events_1h: int,
    multi_chain_native_1h: int,
    market_avg_change_24h: float,
    health_factor: float,
) -> Dict[str, str]:
    return {
        "abnormal_activity": "yes" if erc20_events_1h > 25 or multi_chain_native_1h > 20 else "no",
        "liquidation_watch": "yes" if health_factor < 1.15 else "no",
        "market_stress": "yes" if market_avg_change_24h < -4 else "no",
    }
