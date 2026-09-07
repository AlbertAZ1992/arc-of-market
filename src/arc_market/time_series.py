"""Compact, chart-ready historical series derived from collected market inputs."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from arc_market.models import CollectedMarketData

_EQUITY_COMPONENTS = ("NCBEILQ027S", "FBCELLQ027S")
_DEBT_COMPONENTS = (
    "BCNSDODNS",
    "CMDEBT",
    "FGSDODNS",
    "SLGSDODNS",
    "WCMITCMFODNS",
)


@dataclass(frozen=True)
class _SeriesDefinition:
    series_id: str
    source_ids: tuple[str, ...]
    cadence: str
    basis: str


def _payload(
    definition: _SeriesDefinition,
    values: pd.Series,
    *,
    limit: int = 252,
) -> dict[str, object] | None:
    clean = pd.to_numeric(values, errors="coerce")
    clean = clean.replace([float("inf"), float("-inf")], pd.NA).dropna().sort_index()
    clean = clean[~clean.index.duplicated(keep="last")].tail(limit)
    if len(clean) < 2:
        return None
    points = [
        {
            "asOf": pd.Timestamp(index).date().isoformat(),
            "value": round(float(value), 4),
        }
        for index, value in clean.items()
    ]
    return {
        "seriesId": definition.series_id,
        "sourceIds": list(definition.source_ids),
        "cadence": definition.cadence,
        "basis": definition.basis,
        "startAsOf": points[0]["asOf"],
        "endAsOf": points[-1]["asOf"],
        "points": points,
    }


def _normalized_return(values: pd.Series) -> pd.Series:
    clean = pd.to_numeric(values, errors="coerce").dropna().sort_index().tail(252)
    if clean.empty or float(clean.iloc[0]) <= 0:
        return pd.Series(dtype="float64")
    return clean.div(float(clean.iloc[0])).sub(1).mul(100)


def _mega7_series(prices: pd.DataFrame, members: Sequence[str]) -> pd.Series:
    aligned = prices.loc[:, list(members)].apply(pd.to_numeric, errors="coerce").dropna()
    returns = aligned.pct_change(fill_method=None).dropna().mean(axis="columns")
    return _normalized_return(returns.add(1).cumprod())


def _cyclical_series(prices: pd.DataFrame) -> pd.Series:
    aligned = prices.loc[:, ["XLY", "XLP"]].apply(pd.to_numeric, errors="coerce").dropna()
    return _normalized_return(aligned["XLY"].div(aligned["XLP"]))


def _equity_allocation(observations: dict[str, pd.Series]) -> pd.Series:
    required = (*_EQUITY_COMPONENTS, *_DEBT_COMPONENTS)
    if not set(required).issubset(observations):
        return pd.Series(dtype="float64")
    aligned = pd.concat(
        {series_id: observations[series_id] for series_id in required},
        axis="columns",
        join="inner",
    ).dropna()
    equity = aligned.loc[:, list(_EQUITY_COMPONENTS)].sum(axis="columns")
    total = aligned.loc[:, list(required)].sum(axis="columns")
    share = equity.div(total.where(total != 0)).mul(100)
    share.index = pd.DatetimeIndex(share.index).to_period("Q").to_timestamp("Q")
    return share[~share.index.duplicated(keep="last")].sort_index()


def _core_series(collected: CollectedMarketData, mega7: Sequence[str]) -> list[dict[str, object]]:
    definitions = (
        (
            _SeriesDefinition(
                "mega7-equal-weight",
                ("yahoo-finance",),
                "daily",
                "cumulative_return_pct",
            ),
            _mega7_series(collected.core_prices, mega7),
        ),
        (
            _SeriesDefinition(
                "cyclicals-defensives",
                ("yahoo-finance",),
                "daily",
                "relative_cumulative_return_pct",
            ),
            _cyclical_series(collected.core_prices),
        ),
    )
    return [
        payload
        for definition, values in definitions
        if (payload := _payload(definition, values)) is not None
    ]


def build_time_series(
    collected: CollectedMarketData,
    mega7: Sequence[str],
) -> list[dict[str, object]]:
    result = _core_series(collected, mega7)
    if collected.ofr is not None and collected.ofr.history is not None:
        definition = _SeriesDefinition("financial-stress", ("ofr",), "daily", "index_level")
        payload = _payload(definition, collected.ofr.history["fsi"])
        if payload is not None:
            result.append(payload)
    if collected.fred_series is not None:
        result.extend(_fred_time_series(collected.fred_series))
    if collected.cftc is not None:
        definition = _SeriesDefinition("cot-vix", ("cftc",), "weekly", "net_pct_open_interest")
        payload = _payload(definition, collected.cftc.history["leveragedNetPctOi"], limit=156)
        if payload is not None:
            result.append(payload)
    return result


def _fred_time_series(observations: dict[str, pd.Series]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    definition = _SeriesDefinition("equity-allocation", ("fred",), "quarterly", "allocation_pct")
    payload = _payload(definition, _equity_allocation(observations), limit=120)
    if payload is not None:
        result.append(payload)
    return result
