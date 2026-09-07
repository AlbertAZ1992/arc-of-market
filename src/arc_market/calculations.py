"""Pure calculations for compact public market-data fields."""

import math
from collections.abc import Mapping, Sequence
from datetime import date

import pandas as pd

from arc_market.config import FredDefinition, ParticipationPair
from arc_market.errors import MarketQualityError
from arc_market.models import OfrSnapshot, TreasurySnapshot, VixSnapshot

_WINDOWS = {"return1d": 1, "return1w": 5, "return1m": 20}


def _clean_series(series: pd.Series, minimum: int = 2) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").dropna().sort_index()
    if len(values) < minimum:
        raise MarketQualityError(f"price series has {len(values)} rows; requires {minimum}")
    index = pd.DatetimeIndex([pd.Timestamp(item).tz_localize(None).date() for item in values.index])
    if index.has_duplicates:
        raise MarketQualityError("price sessions must be unique")
    values.index = index
    return values


def _return(series: pd.Series, sessions: int) -> float:
    if len(series) <= sessions:
        raise MarketQualityError(f"price series requires {sessions + 1} sessions")
    return round((float(series.iloc[-1]) / float(series.iloc[-sessions - 1]) - 1) * 100, 4)


def _return_ytd(series: pd.Series) -> float | None:
    current_date = pd.Timestamp(series.index[-1])
    prior_mask = [pd.Timestamp(item).year < current_date.year for item in series.index]
    prior = series.loc[prior_mask]
    if prior.empty:
        return None
    return round((float(series.iloc[-1]) / float(prior.iloc[-1]) - 1) * 100, 4)


def period_returns(series: pd.Series) -> dict[str, float | None]:
    cleaned = _clean_series(series, 21)
    result: dict[str, float | None] = {
        name: _return(cleaned, window) for name, window in _WINDOWS.items()
    }
    result["returnYtd"] = _return_ytd(cleaned)
    return result


def _required_return(returns: Mapping[str, float | None], field: str) -> float:
    value = returns[field]
    if value is None:
        raise MarketQualityError(f"required return is unavailable: {field}")
    return value


def _required_number(row: Mapping[str, object], field: str) -> float:
    value = row[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketQualityError(f"required numeric metric is unavailable: {field}")
    return float(value)


def _above_average(series: pd.Series, window: int) -> bool | None:
    if len(series) < window:
        return None
    average = float(series.tail(window).mean())
    return bool(float(series.iloc[-1]) > average)


def _trend_state(above_ma50: bool | None, above_ma200: bool | None) -> str:
    if above_ma50 is None or above_ma200 is None:
        return "insufficient"
    if above_ma50 and above_ma200:
        return "uptrend"
    if not above_ma50 and not above_ma200:
        return "downtrend"
    return "transition"


def realized_volatility(series: pd.Series, window: int) -> float | None:
    cleaned = _clean_series(series, 2)
    returns = cleaned.pct_change(fill_method=None).dropna()
    if len(returns) < window:
        return None
    value = float(returns.tail(window).std(ddof=1)) * math.sqrt(252) * 100
    return round(value, 4)


def current_drawdown(series: pd.Series, window: int = 252) -> float | None:
    cleaned = _clean_series(series, 2)
    sample = cleaned.tail(window)
    if len(sample) < 2:
        return None
    return round((float(sample.iloc[-1]) / float(sample.max()) - 1) * 100, 4)


def benchmark_metrics(series: pd.Series, benchmark_id: str, ticker: str) -> dict[str, object]:
    cleaned = _clean_series(series, 21)
    above_ma50 = _above_average(cleaned, 50)
    above_ma200 = _above_average(cleaned, 200)
    return {
        "benchmarkId": benchmark_id,
        "proxyTicker": ticker,
        "asOf": pd.Timestamp(cleaned.index[-1]).date().isoformat(),
        **period_returns(cleaned),
        "aboveMa50": above_ma50,
        "aboveMa200": above_ma200,
        "trendState": _trend_state(above_ma50, above_ma200),
        "drawdown52w": current_drawdown(cleaned),
        "realizedVol20d": realized_volatility(cleaned, 20),
        "realizedVol60d": realized_volatility(cleaned, 60),
    }


def trend_snapshot(prices: pd.DataFrame, tickers: Sequence[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ticker in tickers:
        cleaned = _clean_series(prices[ticker], 252)
        value = float(cleaned.iloc[-1])
        averages = {window: float(cleaned.tail(window).mean()) for window in (5, 10, 20, 50)}
        rows.append(
            {
                "ticker": ticker,
                "asOf": pd.Timestamp(cleaned.index[-1]).date().isoformat(),
                "value": round(value, 4),
                "priceBasis": "adjusted_close",
                **{f"ma{window}": round(average, 4) for window, average in averages.items()},
                "aboveMa20": value >= averages[20],
                "aboveMa50": value >= averages[50],
                "distanceMa20Pct": round((value / averages[20] - 1) * 100, 4),
                "distanceMa50Pct": round((value / averages[50] - 1) * 100, 4),
                "drawdown52w": current_drawdown(cleaned),
            }
        )
    return rows


def semiconductor_pulse(
    prices: pd.DataFrame,
    *,
    ticker: str,
    benchmark: str,
) -> dict[str, object]:
    aligned = pd.concat(
        [prices[ticker].rename("semiconductor"), prices[benchmark].rename("benchmark")],
        axis=1,
    ).dropna()
    semiconductor_returns = period_returns(aligned["semiconductor"])
    benchmark_returns = period_returns(aligned["benchmark"])
    result: dict[str, object] = {
        "ticker": ticker,
        "benchmarkTicker": benchmark,
        "asOf": pd.Timestamp(aligned.index[-1]).date().isoformat(),
    }
    for name in _WINDOWS:
        semiconductor = _required_return(semiconductor_returns, name)
        benchmark_value = _required_return(benchmark_returns, name)
        result[name] = semiconductor
        result[f"relativeReturn{name.removeprefix('return')}"] = round(
            semiconductor - benchmark_value,
            4,
        )
    return result


def sector_metrics(
    prices: pd.DataFrame,
    labels: Mapping[str, str],
    *,
    benchmark: str,
) -> list[dict[str, object]]:
    benchmark_return = _required_return(period_returns(prices[benchmark]), "return1m")
    rows: list[dict[str, object]] = []
    for ticker, label in labels.items():
        returns = period_returns(prices[ticker])
        relative = round(_required_return(returns, "return1m") - benchmark_return, 4)
        as_of = pd.Timestamp(_clean_series(prices[ticker]).index[-1]).date().isoformat()
        rows.append(
            {"ticker": ticker, "label": label, "asOf": as_of, **returns, "relative1m": relative}
        )
    rows.sort(key=lambda item: (-_required_number(item, "relative1m"), str(item["ticker"])))
    return [{**item, "rank": rank} for rank, item in enumerate(rows, start=1)]


def mega7_metrics(prices: pd.DataFrame, members: Sequence[str]) -> dict[str, object]:
    spy_return = _required_return(period_returns(prices["SPY"]), "return1m")
    qqq_return = _required_return(period_returns(prices["QQQ"]), "return1m")
    rows: list[dict[str, object]] = []
    member_returns: dict[str, dict[str, float | None]] = {}
    for ticker in members:
        returns = period_returns(prices[ticker])
        member_returns[ticker] = returns
        rows.append(
            {
                "ticker": ticker,
                "asOf": pd.Timestamp(_clean_series(prices[ticker]).index[-1]).date().isoformat(),
                **returns,
                "relativeSpy1m": round(_required_return(returns, "return1m") - spy_return, 4),
                "relativeQqq1m": round(_required_return(returns, "return1m") - qqq_return, 4),
            }
        )
    rows.sort(key=lambda item: (-_required_number(item, "relativeSpy1m"), str(item["ticker"])))
    ranked = [{**item, "rank": rank} for rank, item in enumerate(rows, start=1)]
    equal_weight = {
        field: round(
            sum(_required_return(member_returns[ticker], field) for ticker in members)
            / len(members),
            4,
        )
        for field in (*_WINDOWS, "returnYtd")
        if all(member_returns[ticker][field] is not None for ticker in members)
    }
    return {"basketVersion": "mega7-2026-01", "members": ranked, "equalWeight": equal_weight}


def _eligible_above(prices: pd.DataFrame, ticker: str, window: int) -> bool | None:
    if ticker not in prices:
        return None
    series = pd.to_numeric(prices[ticker], errors="coerce").dropna().sort_index()
    if len(series) < window or series.index[-1] != prices.index[-1]:
        return None
    return bool(float(series.iloc[-1]) > float(series.tail(window).mean()))


def _breadth_state(ma50: float, ma200: float) -> str:
    if ma50 >= 60 and ma200 >= 60:
        return "strong"
    if ma50 < 50 and ma200 < 50:
        return "weak"
    return "mixed"


def breadth_metrics(
    index_id: str,
    members: Sequence[str],
    prices: pd.DataFrame,
    *,
    observed_at: date,
    minimum_coverage: float,
) -> dict[str, object]:
    unique_members = tuple(dict.fromkeys(members))
    ma50 = [_eligible_above(prices, ticker, 50) for ticker in unique_members]
    ma200 = [_eligible_above(prices, ticker, 200) for ticker in unique_members]
    eligible50 = [value for value in ma50 if value is not None]
    eligible200 = [value for value in ma200 if value is not None]
    if not unique_members or len(eligible200) / len(unique_members) < minimum_coverage:
        raise MarketQualityError(f"{index_id} MA200 coverage is below {minimum_coverage:.0%}")
    pct50 = round(sum(eligible50) / len(eligible50) * 100, 2)
    pct200 = round(sum(eligible200) / len(eligible200) * 100, 2)
    return {
        "indexId": index_id,
        "asOf": pd.Timestamp(prices.index[-1]).date().isoformat(),
        "universeObservedAt": observed_at.isoformat(),
        "universeCount": len(unique_members),
        "eligibleCountMa50": len(eligible50),
        "eligibleCountMa200": len(eligible200),
        "pctAboveMa50": pct50,
        "pctAboveMa200": pct200,
        "breadthState": _breadth_state(pct50, pct200),
        "caveat": "current-universe survivorship bias",
    }


def vix_regime(value: float) -> str:
    if value < 15:
        return "low"
    if value < 25:
        return "neutral"
    if value < 35:
        return "elevated"
    return "stress"


def participation_metrics(
    prices: pd.DataFrame,
    pairs: Sequence[ParticipationPair],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for pair in pairs:
        equal_ticker = str(pair.equal_weight_ticker)
        cap_ticker = str(pair.cap_weight_ticker)
        pair_id = str(pair.pair_id)
        aligned = pd.concat(
            [prices[equal_ticker].rename("equal"), prices[cap_ticker].rename("cap")],
            axis=1,
        ).dropna()
        if len(aligned) < 50:
            raise MarketQualityError(f"participation pair {pair_id} requires 50 sessions")
        equal_return = _return(aligned["equal"], 20)
        cap_return = _return(aligned["cap"], 20)
        ratio = aligned["equal"] / aligned["cap"]
        relative = round(equal_return - cap_return, 4)
        above_ma50 = bool(float(ratio.iloc[-1]) > float(ratio.tail(50).mean()))
        state = "broadening" if relative > 0 and above_ma50 else "narrowing"
        if (relative > 0) != above_ma50:
            state = "mixed"
        rows.append(
            {
                "pairId": pair_id,
                "equalWeightTicker": equal_ticker,
                "capWeightTicker": cap_ticker,
                "asOf": pd.Timestamp(aligned.index[-1]).date().isoformat(),
                "relativeReturn1m": relative,
                "ratioAboveMa50": above_ma50,
                "participationState": state,
            }
        )
    return rows


def _cross_state(current: float, previous: float) -> str:
    if previous <= 0 < current:
        return "UP"
    if previous >= 0 > current:
        return "DOWN"
    return "NONE"


def roc35_metrics(
    prices: pd.DataFrame,
    *,
    value_ticker: str,
    growth_ticker: str,
    lookback_sessions: int,
) -> dict[str, object]:
    aligned = pd.concat(
        [prices[value_ticker].rename("value"), prices[growth_ticker].rename("growth")],
        axis=1,
    ).dropna()
    minimum = lookback_sessions + 6
    if len(aligned) < minimum:
        raise MarketQualityError(f"ROC35 requires at least {minimum} aligned sessions")
    ratio = aligned["value"] / aligned["growth"]

    def rolling_value(index: int) -> float:
        base = index - lookback_sessions
        return round((float(ratio.iloc[index]) / float(ratio.iloc[base]) - 1) * 100, 4)

    current_index = len(aligned) - 1
    current = rolling_value(current_index)
    previous = rolling_value(current_index - 1)
    comparison_index = current_index - lookback_sessions
    recent = [
        {
            "asOf": pd.Timestamp(aligned.index[index]).date().isoformat(),
            "value": rolling_value(index),
        }
        for index in range(current_index - 4, current_index + 1)
    ]
    return {
        "indicatorId": "roc35",
        "engineVersion": "1.0.0",
        "valueTicker": value_ticker,
        "growthTicker": growth_ticker,
        "asOf": pd.Timestamp(aligned.index[current_index]).date().isoformat(),
        "comparisonAsOf": pd.Timestamp(aligned.index[comparison_index]).date().isoformat(),
        "value": current,
        "previousValue": previous,
        "change1dPp": round(current - previous, 4),
        "ratio": round(float(ratio.iloc[current_index]), 6),
        "ratioChange1dPct": round(
            (float(ratio.iloc[current_index]) / float(ratio.iloc[current_index - 1]) - 1) * 100,
            4,
        ),
        "direction": "RISING"
        if current > previous
        else "FALLING"
        if current < previous
        else "FLAT",
        "zeroCross": _cross_state(current, previous),
        "distanceFromZeroPp": current,
        "recent": recent,
        "evidence": {
            "current": {
                "asOf": pd.Timestamp(aligned.index[current_index]).date().isoformat(),
                "valueAdjustedClose": round(float(aligned.iloc[current_index]["value"]), 4),
                "growthAdjustedClose": round(float(aligned.iloc[current_index]["growth"]), 4),
            },
            "comparison": {
                "asOf": pd.Timestamp(aligned.index[comparison_index]).date().isoformat(),
                "valueAdjustedClose": round(float(aligned.iloc[comparison_index]["value"]), 4),
                "growthAdjustedClose": round(float(aligned.iloc[comparison_index]["growth"]), 4),
            },
        },
    }


def risk_state(realized_vol20d: float | None, drawdown: float | None) -> str:
    if realized_vol20d is None or drawdown is None:
        return "insufficient"
    if realized_vol20d >= 30 or drawdown <= -15:
        return "stress"
    if realized_vol20d >= 20 or drawdown <= -8:
        return "elevated"
    if realized_vol20d < 15 and drawdown > -5:
        return "calm"
    return "normal"


def risk_metrics(spy: pd.Series, vix: VixSnapshot | None) -> dict[str, object]:
    vol20 = realized_volatility(spy, 20)
    vol60 = realized_volatility(spy, 60)
    drawdown = current_drawdown(spy)
    previous = vix.previous_value if vix else None
    change = None if vix is None or previous is None else round((vix.value / previous - 1) * 100, 4)
    return {
        "asOf": pd.Timestamp(_clean_series(spy).index[-1]).date().isoformat(),
        "realizedVol20d": vol20,
        "realizedVol60d": vol60,
        "currentDrawdown": drawdown,
        "riskState": risk_state(vol20, drawdown),
        "vixValue": vix.value if vix else None,
        "vixAsOf": vix.as_of.isoformat() if vix else None,
        "vixPreviousValue": previous,
        "vixPreviousAsOf": vix.previous_as_of.isoformat() if vix and vix.previous_as_of else None,
        "vixChange1dPct": change,
        "vixRegime": vix_regime(vix.value) if vix else None,
    }


def treasury_curve_metrics(snapshot: TreasurySnapshot | None) -> dict[str, object]:
    if snapshot is None:
        return {}
    return {
        "asOf": snapshot.as_of.isoformat(),
        "treasury2y": snapshot.treasury_2y,
        "treasury10y": snapshot.treasury_10y,
        "curve2s10s": round(snapshot.treasury_10y - snapshot.treasury_2y, 4),
        "treasury2yChange1dBp": snapshot.treasury_2y_change_1d_bp,
        "treasury10yChange1dBp": snapshot.treasury_10y_change_1d_bp,
        "treasury10yChange3dBp": snapshot.treasury_10y_change_3d_bp,
    }


def _fred_value(series: pd.Series, transform: str) -> float:
    cleaned = _clean_series(series, 2)
    if transform == "latest":
        return round(float(cleaned.iloc[-1]), 4)
    if transform == "change":
        return round(float(cleaned.iloc[-1] - cleaned.iloc[-2]), 4)
    if transform == "millions_to_trillions":
        return round(float(cleaned.iloc[-1]) / 1_000_000, 4)
    if transform == "yoy":
        if len(cleaned) < 13:
            raise MarketQualityError("FRED year-over-year transform requires 13 observations")
        return round((float(cleaned.iloc[-1]) / float(cleaned.iloc[-13]) - 1) * 100, 4)
    raise MarketQualityError(f"unknown FRED transform: {transform}")


def macro_metrics(
    series: Mapping[str, pd.Series], definitions: Mapping[str, FredDefinition]
) -> dict[str, object]:
    result = {}
    for key, definition in definitions.items():
        if definition.transform == "component":
            continue
        series_id = str(definition.series_id)
        source = _clean_series(series[series_id], 2)
        result[key] = {
            "value": _fred_value(source, str(definition.transform)),
            "asOf": pd.Timestamp(source.index[-1]).date().isoformat(),
            "unit": str(definition.unit),
            "sourceSeries": series_id,
            "vintage": "latest revised; not point-in-time safe",
        }
    if {"DGS10", "DFII10"}.issubset(series):
        nominal = _clean_series(series["DGS10"], 2)
        real = _clean_series(series["DFII10"], 2)
        aligned = pd.concat([nominal.rename("nominal"), real.rename("real")], axis=1).dropna()
        result["breakeven10y"] = {
            "value": round(float(aligned.iloc[-1]["nominal"] - aligned.iloc[-1]["real"]), 4),
            "asOf": pd.Timestamp(aligned.index[-1]).date().isoformat(),
            "unit": "percentage_points",
            "sourceSeries": ["DGS10", "DFII10"],
            "vintage": "latest revised; not point-in-time safe",
        }
    return result


def financial_stress_metrics(snapshot: OfrSnapshot) -> dict[str, object]:
    if snapshot.value < -1:
        state = "low"
    elif snapshot.value < 1:
        state = "normal"
    elif snapshot.value < 2:
        state = "elevated"
    else:
        state = "stress"
    return {
        "asOf": snapshot.as_of.isoformat(),
        "value": snapshot.value,
        "components": snapshot.components,
        "regions": snapshot.regions,
        "stressState": state,
        "vintage": "latest revised; not point-in-time safe",
    }
