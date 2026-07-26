"""Pure transformations for long-horizon index research charts."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, cast

import pandas as pd

ANNUAL_BANDS = (
    (None, -30.0, "<-30%"),
    (-30.0, -20.0, "-30~-20%"),
    (-20.0, -10.0, "-20~-10%"),
    (-10.0, 0.0, "-10~0%"),
    (0.0, 10.0, "0~10%"),
    (10.0, 20.0, "10~20%"),
    (20.0, 30.0, "20~30%"),
    (30.0, None, ">30%"),
)
DAILY_BANDS = (
    (None, -5.0, "<-5%"),
    (-5.0, -3.0, "-5~-3%"),
    (-3.0, -2.0, "-3~-2%"),
    (-2.0, -1.0, "-2~-1%"),
    (-1.0, 0.0, "-1~0%"),
    (0.0, 1.0, "0~1%"),
    (1.0, 2.0, "1~2%"),
    (2.0, 3.0, "2~3%"),
    (3.0, 5.0, "3~5%"),
    (5.0, None, ">5%"),
)


def _timestamp(value: Any) -> pd.Timestamp:
    return cast(pd.Timestamp, pd.Timestamp(value))


def _inside_band(value: float, lower: float | None, upper: float | None) -> bool:
    lower_matches = lower is None or value >= lower
    upper_matches = upper is None or value < upper
    return lower_matches and upper_matches


def drawdown_history(close: pd.Series) -> tuple[pd.Series, list[dict[str, Any]]]:
    """Return drawdowns and each peak-to-recovery episode."""
    values = close.dropna().sort_index()
    if values.empty:
        return pd.Series(dtype=float), []

    drawdowns = values.div(values.cummax()).sub(1)
    peak_date = _timestamp(values.index[0])
    peak_value = float(values.iloc[0])
    trough_date = peak_date
    trough_value = peak_value
    episodes: list[dict[str, Any]] = []

    for raw_date, raw_value in values.iloc[1:].items():
        observation_date = _timestamp(raw_date)
        observation_value = float(raw_value)
        if observation_value >= peak_value:
            if trough_value < peak_value:
                episodes.append(
                    _drawdown_episode(
                        peak_date,
                        peak_value,
                        trough_date,
                        trough_value,
                        observation_date,
                    )
                )
            peak_date = observation_date
            peak_value = observation_value
            trough_date = observation_date
            trough_value = observation_value
        elif observation_value < trough_value:
            trough_date = observation_date
            trough_value = observation_value

    if trough_value < peak_value:
        episodes.append(
            _drawdown_episode(
                peak_date,
                peak_value,
                trough_date,
                trough_value,
                recovery_date=None,
            )
        )
    return drawdowns, episodes


def _drawdown_episode(
    peak_date: pd.Timestamp,
    peak_value: float,
    trough_date: pd.Timestamp,
    trough_value: float,
    recovery_date: pd.Timestamp | None,
) -> dict[str, Any]:
    return {
        "peak": peak_date.strftime("%Y-%m-%d"),
        "trough": trough_date.strftime("%Y-%m-%d"),
        "recovery": recovery_date.strftime("%Y-%m-%d") if recovery_date else None,
        "depth": round((trough_value / peak_value - 1) * 100, 2),
    }


def annual_return_distribution(
    close: pd.Series,
    current_year: int | None = None,
) -> dict[str, Any]:
    year_limit = current_year or datetime.now(UTC).year
    annual_returns = close.resample("YE").last().pct_change().mul(100).dropna()
    completed = annual_returns[annual_returns.index.year < year_limit]
    buckets = []
    for lower, upper, label in ANNUAL_BANDS:
        years = [
            int(date.year)
            for date, value in completed.items()
            if _inside_band(float(value), lower, upper)
        ]
        buckets.append({"label": label, "count": len(years), "years": sorted(years)})
    return {
        "buckets": buckets,
        "years_total": int(completed.size),
        "return_type": "price",
    }


def annual_performance(close: pd.Series) -> dict[str, Any]:
    annual_returns = close.resample("YE").last().pct_change().mul(100).dropna()
    latest_date = _timestamp(close.index[-1])
    current_year = datetime.now(UTC).year
    return {
        "years": [int(_timestamp(date).year) for date in annual_returns.index],
        "returns": [round(float(value), 2) for value in annual_returns],
        "partial_year": latest_date.year if latest_date.year == current_year else None,
        "as_of": latest_date.strftime("%Y-%m-%d"),
        "return_type": "price",
    }


def intrayear_performance(close: pd.Series) -> dict[str, Any]:
    """Compare each completed year's return with its worst path from prior year-end."""
    values = close.dropna().sort_index()
    annual_returns = values.resample("YE").last().pct_change().mul(100).dropna()
    returns_by_year = {
        _timestamp(date).year: float(value) for date, value in annual_returns.items()
    }
    year_labels = pd.Series(
        [_timestamp(date).year for date in values.index],
        index=values.index,
    )
    current_year = datetime.now(UTC).year
    rows = []
    for year in sorted(returns_by_year):
        within_year = values.loc[year_labels.eq(year)]
        earlier = values.loc[year_labels.lt(year)]
        if within_year.size < 60 or earlier.empty:
            continue
        path = pd.concat([earlier.iloc[[-1]], within_year])
        worst_path = path.div(path.cummax()).sub(1).min() * 100
        rows.append(
            {
                "year": year,
                "intra_dd": round(float(worst_path), 1),
                "ret": round(returns_by_year[year], 1),
                "partial_year": year == current_year,
            }
        )
    return {"rows": rows, "return_type": "price"}


def rolling_five_year_performance(month_end: pd.Series) -> dict[str, Any]:
    cagr = month_end.div(month_end.shift(60)).pow(0.2).sub(1).mul(100).dropna()
    return {
        "dates": [_timestamp(date).strftime("%Y-%m-%d") for date in cagr.index],
        "cagr": [round(float(value), 2) for value in cagr],
        "return_type": "price",
    }


def volatility_history(
    close: pd.Series,
    volatility_index: pd.Series | None = None,
    volatility_name: str = "",
) -> dict[str, Any]:
    daily_returns = close.pct_change()
    scale = 252**0.5 * 100
    measures = pd.DataFrame(
        {
            "vol20": daily_returns.rolling(20).std().mul(scale),
            "vol60": daily_returns.rolling(60).std().mul(scale),
        }
    )
    measures = measures.dropna(how="all")
    week_keys = pd.DatetimeIndex(measures.index).to_period("W-SUN")
    weekly = measures.groupby(week_keys).tail(1).dropna(subset=["vol20"])
    payload: dict[str, Any] = {
        "dates": [_timestamp(date).strftime("%Y-%m-%d") for date in weekly.index],
        "vol20": [round(float(value), 2) for value in weekly["vol20"]],
        "vol60": [round(float(value), 2) for value in weekly["vol60"]],
        "vol_index_name": volatility_name,
        "return_type": "price",
    }
    if volatility_index is not None:
        index_values = volatility_index.dropna()
        index_weeks = pd.DatetimeIndex(index_values.index).to_period("W-SUN")
        weekly_index = index_values.groupby(index_weeks).tail(1)
        weekly_index.index = pd.DatetimeIndex(weekly_index.index).to_period("W-SUN")
        target_weeks = pd.DatetimeIndex(weekly.index).to_period("W-SUN")
        aligned = weekly_index.reindex(target_weeks)
        payload["vol_index"] = [
            None if pd.isna(value) else round(float(value), 2) for value in aligned
        ]
    return payload


def monthly_seasonality(month_end: pd.Series) -> dict[str, Any]:
    returns = month_end.pct_change().mul(100).dropna()
    rows = []
    for month in range(1, 13):
        month_matches = [_timestamp(date).month == month for date in returns.index]
        observations = returns.loc[month_matches]
        rows.append(
            {
                "month": month,
                "avg": round(float(cast(Any, observations.mean())), 2),
                "win": round(float(observations.gt(0).mean() * 100), 1),
            }
        )
    return {
        "rows": rows,
        "years": f"{month_end.index[0].year}–{month_end.index[-1].year}",
        "return_type": "price",
    }


def holding_period_summary(
    month_end: pd.Series,
    horizons: tuple[int, ...] = (1, 3, 5, 10, 20),
) -> dict[str, Any]:
    rows = []
    for years in horizons:
        observations = month_end.div(month_end.shift(12 * years))
        annualized = observations.pow(1 / years).sub(1).mul(100).dropna()
        if annualized.size < 24:
            continue
        rows.append(
            {
                "years": years,
                "win": round(float(annualized.gt(0).mean() * 100), 1),
                "median": round(float(annualized.median()), 1),
                "worst": round(float(annualized.min()), 1),
                "best": round(float(annualized.max()), 1),
                "samples": int(annualized.size),
            }
        )
    return {"rows": rows, "return_type": "price"}


def rolling_cagr_payload(
    month_end: pd.Series,
    horizons: tuple[int, ...] = (5, 10, 20),
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "dates": [_timestamp(date).strftime("%Y-%m-%d") for date in month_end.index],
        "return_type": "price",
    }
    for years in horizons:
        annualized = month_end.div(month_end.shift(12 * years)).pow(1 / years).sub(1).mul(100)
        payload[f"cagr{years}"] = [
            None if pd.isna(value) else round(float(value), 2) for value in annualized
        ]
    return payload


def extreme_day_summary(close: pd.Series, count: int = 12) -> dict[str, Any]:
    returns = close.pct_change().mul(100).dropna()
    histogram = []
    for lower, upper, label in DAILY_BANDS:
        matches = sum(_inside_band(float(value), lower, upper) for value in returns)
        histogram.append({"label": label, "count": matches})
    return {
        "worst": [_dated_return(item) for item in returns.nsmallest(count).items()],
        "best": [_dated_return(item) for item in returns.nlargest(count).items()],
        "hist": histogram,
        "days_total": int(returns.size),
        "return_type": "price",
    }


def _dated_return(item: tuple[Any, Any]) -> dict[str, Any]:
    date, value = item
    return {"date": _timestamp(date).strftime("%Y-%m-%d"), "ret": round(float(value), 2)}


@dataclass
class TurningPoint:
    date: pd.Timestamp
    value: float


def market_cycles(
    close: pd.Series,
    bear_decline: float = 0.20,
    bull_advance: float = 0.25,
) -> dict[str, Any]:
    """Detect threshold-confirmed market cycles from daily closes."""
    values = close.dropna().sort_index()
    if values.empty:
        return {"cycles": [], "return_type": "price"}

    mode: Literal["peak", "trough"] = "peak"
    candidate = TurningPoint(_timestamp(values.index[0]), float(values.iloc[0]))
    turning_points: list[TurningPoint] = []
    for raw_date, raw_value in values.iloc[1:].items():
        current = TurningPoint(_timestamp(raw_date), float(raw_value))
        if mode == "peak":
            candidate = current if current.value > candidate.value else candidate
            if current.value <= candidate.value * (1 - bear_decline):
                turning_points.append(candidate)
                candidate = current
                mode = "trough"
        else:
            candidate = current if current.value < candidate.value else candidate
            if current.value >= candidate.value * (1 + bull_advance):
                turning_points.append(candidate)
                candidate = current
                mode = "peak"

    first = TurningPoint(_timestamp(values.index[0]), float(values.iloc[0]))
    last = TurningPoint(_timestamp(values.index[-1]), float(values.iloc[-1]))
    cycles = []
    start = first
    for end in turning_points:
        if end.date > start.date:
            cycles.append(_cycle_row(start, end, complete=True))
            start = end
    cycles.append(_cycle_row(start, last, complete=False))
    return {"cycles": cycles, "return_type": "price"}


def _cycle_row(start: TurningPoint, end: TurningPoint, *, complete: bool) -> dict[str, Any]:
    change = (end.value / start.value - 1) * 100
    return {
        "kind": "bull" if change > 0 else "bear",
        "start": start.date.strftime("%Y-%m-%d"),
        "end": end.date.strftime("%Y-%m-%d") if complete else None,
        "ret": round(change, 1),
        "days": int((end.date - start.date).days),
    }
