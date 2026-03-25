"""
Prediction Model — linear regression on recent price history using NumPy only (no sklearn).
Fits y = a + b*t on tick index; forecasts next step and reports R².
"""
from typing import Dict, List

import numpy as np


def _forecast_series(series: List[float]) -> Dict[str, float]:
    if len(series) < 5:
        return {}
    t = np.arange(len(series), dtype=float)
    y = np.array(series, dtype=float)
    # OLS with intercept: y = a + b*t
    X = np.column_stack([np.ones(len(t)), t])
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    a, b = float(coef[0]), float(coef[1])
    t_next = float(len(series))
    pred_next = a + b * t_next
    y_hat = X @ coef
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = (1.0 - ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
    r2 = max(0.0, min(1.0, r2))
    return {
        "next_step_estimate": pred_next,
        "slope_per_tick": b,
        "direction": "up" if b > 0 else "down",
        "r2_fit": r2,
        "confidence": r2,
    }


def predict_price_trends(
    asset_history: List[dict],
    tokens: List[str],
) -> Dict[str, dict]:
    """
    asset_history: rows from agent memory with keys timestamp, ETH, BTC, ...
    """
    if not asset_history or len(asset_history) < 6:
        return {}

    out: Dict[str, dict] = {}
    for t in tokens:
        series = []
        for row in asset_history:
            if t in row and row[t] is not None:
                try:
                    series.append(float(row[t]))
                except (TypeError, ValueError):
                    continue
        if len(series) < 6:
            continue
        tail = series[-40:]
        fc = _forecast_series(tail)
        if fc:
            fc["lookback_points"] = len(tail)
            out[t] = fc
    return out
