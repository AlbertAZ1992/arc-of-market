"""Compact, unrounded inputs for the independent Core Rotation strategy engine."""

import hashlib
import json
import math
import struct

import pandas as pd


def core_rotation_inputs(prices: pd.DataFrame) -> dict[str, object] | None:
    if not {"QQQ", "VTV"}.issubset(prices.columns) or len(prices) < 271:
        return None
    sample = prices.loc[:, ["QQQ", "VTV"]].tail(271).apply(pd.to_numeric, errors="coerce")
    if sample.index.has_duplicates or not sample.index.is_monotonic_increasing:
        return None
    if not all(math.isfinite(value) for value in sample.to_numpy().flat):
        return None
    if (sample <= 0).any().any():
        return None
    qqq = sample["QQQ"]
    ratio = sample["VTV"] / qqq
    high = qqq.rolling(252, min_periods=252).max()
    recent_high = bool((qqq.tail(20) / high.tail(20) >= 0.95).any())
    values = {
        "asOf": pd.Timestamp(sample.index[-1]).date().isoformat(),
        "previousSession": pd.Timestamp(sample.index[-2]).date().isoformat(),
        "roc35": (float(ratio.iloc[-1]) / float(ratio.iloc[-36]) - 1) * 100,
        "value": float(qqq.iloc[-1]),
        "ma50": float(qqq.tail(50).mean()),
        "ma200": float(qqq.tail(200).mean()),
        "ma50FiveSessionsAgo": float(qqq.iloc[:-5].tail(50).mean()),
        "recentHigh": recent_high,
    }
    normalized = {
        key: {"$float64": struct.pack(">d", value).hex()} if isinstance(value, float) else value
        for key, value in values.items()
    }
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return {**values, "calculationDigest": hashlib.sha256(encoded.encode()).hexdigest()}
