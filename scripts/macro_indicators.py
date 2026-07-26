"""Pure transformations for macroeconomic research indicators."""

from typing import Any, cast

import pandas as pd


def equity_allocation_share(
    observations: dict[str, pd.Series],
    equity_series: tuple[str, ...],
    debt_series: tuple[str, ...],
) -> pd.Series:
    """Calculate equity value as a share of equity plus selected debt liabilities."""
    required = (*equity_series, *debt_series)
    missing = sorted(set(required) - observations.keys())
    if missing:
        raise ValueError(f"missing allocation components: {', '.join(missing)}")
    aligned = pd.concat(
        {series_id: observations[series_id] for series_id in required},
        axis="columns",
        join="inner",
    ).dropna()
    if aligned.empty:
        raise ValueError("allocation components have no common observation dates")
    equity_value = aligned.loc[:, list(equity_series)].sum(axis="columns")
    total_value = aligned.loc[:, list(required)].sum(axis="columns")
    share = equity_value.div(total_value).dropna()
    quarter_end = pd.DatetimeIndex(share.index).to_period("Q").to_timestamp("Q")
    share.index = quarter_end
    return share[~share.index.duplicated(keep="last")].sort_index()


def latest_percentile(values: pd.Series) -> float:
    clean = values.dropna()
    if clean.empty:
        raise ValueError("cannot rank an empty series")
    latest = float(clean.iloc[-1])
    return round(float(clean.le(latest).mean() * 100), 1)


def equity_allocation_payload(
    values: pd.Series,
    component_ids: tuple[str, ...],
) -> dict[str, Any]:
    if values.empty:
        raise ValueError("equity allocation share is empty")
    latest = float(values.iloc[-1])
    latest_date = cast(pd.Timestamp, pd.Timestamp(values.index[-1]))
    return {
        "meta": {
            "name": "美国金融资产股票配置占比",
            "description": "比较股票市值与股票市值加指定债务余额的比例。",
            "formula": "equity market value / (equity market value + selected debt liabilities)",
            "component_series": list(component_ids),
            "component_units": "millions of dollars",
            "component_count": len(component_ids),
            "range_check": 0.0 <= latest <= 1.0,
            "current_value": round(latest, 4),
            "current_percentile": latest_percentile(values),
            "as_of": latest_date.strftime("%Y-%m-%d"),
            "availability": (
                "Latest revised FRED observations. The series is descriptive and is not "
                "suitable for point-in-time backtests without vintage data."
            ),
        },
        "dates": [pd.Timestamp(date).strftime("%Y-%m-%d") for date in values.index],
        "values": [round(float(value), 4) for value in values],
    }
