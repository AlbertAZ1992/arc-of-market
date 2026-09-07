"""Reconstruct dated public rotation observations, separately from live publication."""

import hashlib
import json
import math
from datetime import date, datetime

import pandas as pd

from arc_market.calculations import roc35_metrics, trend_snapshot
from arc_market.strategy_inputs import core_rotation_inputs


def build_rotation_history(
    prices: pd.DataFrame, *, start: date, end: date, computed_at: datetime
) -> dict[str, object]:
    if start > end or computed_at.tzinfo is None:
        raise ValueError("A valid date range and timezone-aware computation time are required")
    frame = _validated_prices(prices.loc[prices.index <= pd.Timestamp(end)])
    dates = frame.index[frame.index >= pd.Timestamp(start)]
    if len(dates) == 0 or len(frame.loc[: dates[0]]) < 271:
        raise ValueError("History requires a nonempty range and 271 warmup sessions")
    entries = [_observation(frame.loc[:as_of], computed_at) for as_of in dates]
    return {"schemaVersion": "1.0", "signalId": "roc35", "entries": entries}


def _validated_prices(prices: pd.DataFrame) -> pd.DataFrame:
    if not {"QQQ", "VTV"}.issubset(prices.columns):
        raise ValueError("QQQ and VTV are required")
    frame = prices.loc[:, ["QQQ", "VTV"]].apply(pd.to_numeric, errors="coerce")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("Session dates must be unique and ordered")
    if not all(math.isfinite(value) and value > 0 for value in frame.to_numpy().flat):
        raise ValueError("Every aligned session must have positive finite prices")
    return frame


def _number(value: object) -> float:
    if not isinstance(value, int | float) or not math.isfinite(value):
        raise ValueError("Calculation did not return a finite number")
    return float(value)


def _state(value: float) -> str:
    if value == 0:
        return "NEUTRAL"
    return "VALUE_LEADING" if value > 0 else "GROWTH_LEADING"


def _event(state: str, previous: str) -> str:
    if state == previous:
        return "UNCHANGED"
    if state == "NEUTRAL":
        return "TOUCHED_ZERO"
    return "CROSSED_UP" if state == "VALUE_LEADING" else "CROSSED_DOWN"


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _rising_streak(frame: pd.DataFrame) -> int:
    ratio = frame["VTV"] / frame["QQQ"]
    roc = ((ratio / ratio.shift(35) - 1) * 100).round(4)
    streak = 0
    for change in reversed(roc.diff().dropna().tolist()):
        if change <= 0:
            break
        streak += 1
    return streak


def _observation(frame: pd.DataFrame, computed_at: datetime) -> dict[str, object]:
    style = roc35_metrics(frame, value_ticker="VTV", growth_ticker="QQQ", lookback_sessions=35)
    trend = trend_snapshot(frame, ("QQQ",))[0]
    value, previous = _number(style["value"]), _number(style["previousValue"])
    state, previous_state = _state(value), _state(previous)
    input_digest = _digest(
        [[str(index), float(row["QQQ"]), float(row["VTV"])] for index, row in frame.iterrows()]
    )
    strategy_inputs = core_rotation_inputs(frame)
    if strategy_inputs is None:
        raise ValueError("Core Rotation inputs are unavailable for a reconstructed session")
    observation = {
        "asOf": style["asOf"],
        "value": f"{value:.4f}",
        "state": state,
        "previousState": previous_state,
        "direction": style["direction"],
        "event": _event(state, previous_state),
        "pendulum": {
            "value": value,
            "previousValue": previous,
            "change1d": style["change1dPp"],
            "direction": style["direction"],
            "state": state,
            "risingStreak": _rising_streak(frame),
        },
        "qqq": {
            key: trend[key]
            for key in (
                "value",
                "ma20",
                "ma50",
                "distanceMa20Pct",
                "distanceMa50Pct",
            )
        },
        "strategyInputs": strategy_inputs,
    }
    return {
        **observation,
        "releaseId": f"sr_reconstructed_{_digest(observation)}",
        "reconstruction": {
            "computedAt": computed_at.isoformat(),
            "methodology": "roc35@1.0.0",
            "source": "Yahoo Finance · adjusted daily close",
            "inputDigest": input_digest,
        },
    }
