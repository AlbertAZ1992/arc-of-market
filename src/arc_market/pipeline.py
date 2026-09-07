"""Compose normalized inputs into one compact Market Release core."""

import pandas as pd

from arc_market.calculations import (
    benchmark_metrics,
    breadth_metrics,
    financial_stress_metrics,
    macro_metrics,
    mega7_metrics,
    participation_metrics,
    risk_metrics,
    roc35_metrics,
    sector_metrics,
    semiconductor_pulse,
    treasury_curve_metrics,
    trend_snapshot,
)
from arc_market.config import MarketConfig
from arc_market.indicators import build_indicator_snapshot
from arc_market.models import CollectedMarketData, SourceStatus
from arc_market.strategy_inputs import core_rotation_inputs
from arc_market.time_series import build_time_series


def _source_entry(config: MarketConfig, status: SourceStatus) -> dict[str, object]:
    source = config.sources.get(status.source_id, {})
    return {
        **status.to_dict(),
        "url": source.get("url"),
        "publishPolicy": source.get("publishPolicy"),
        "attribution": source.get("attribution"),
    }


def _breadth(config: MarketConfig, collected: CollectedMarketData) -> list[dict[str, object]]:
    rows = []
    for index_id, definition in config.breadth.items():
        item = collected.breadth.get(index_id)
        if item is None:
            continue
        rows.append(
            breadth_metrics(
                index_id,
                item.universe.members,
                item.prices,
                observed_at=item.universe.observed_at,
                minimum_coverage=definition.minimum_coverage,
            )
        )
    return rows


def _market_history(
    prices: pd.DataFrame,
    benchmarks: dict[str, str],
    *,
    sessions: int = 252,
) -> list[dict[str, object]]:
    history: list[dict[str, object]] = []
    for benchmark_id, ticker in benchmarks.items():
        series = pd.to_numeric(prices[ticker], errors="coerce").dropna().sort_index().tail(sessions)
        if len(series) < 2:
            continue
        starting_value = float(series.iloc[0])
        if starting_value <= 0:
            continue
        points: list[dict[str, object]] = [
            {
                "asOf": pd.Timestamp(index).date().isoformat(),
                "value": round((float(value) / starting_value - 1) * 100, 4),
            }
            for index, value in series.items()
        ]
        history.append(
            {
                "benchmarkId": benchmark_id,
                "proxyTicker": ticker,
                "basis": "cumulative_return_pct",
                "startAsOf": points[0]["asOf"],
                "endAsOf": points[-1]["asOf"],
                "points": points,
            }
        )
    return history


def build_release_core(
    config: MarketConfig,
    collected: CollectedMarketData,
    *,
    producer_commit: str,
) -> dict[str, object]:
    market_overview = [
        benchmark_metrics(collected.core_prices[ticker], benchmark_id, ticker)
        for benchmark_id, ticker in config.benchmarks.items()
    ]
    failed = any(status.status == "FAILED" for status in collected.source_status)
    data: dict[str, object] = {
        "marketOverview": market_overview,
        "marketHistory": _market_history(collected.core_prices, config.benchmarks),
        "trendSnapshot": trend_snapshot(collected.core_prices, ("SPY", "QQQ")),
        "coreRotationInputs": core_rotation_inputs(collected.core_prices),
        "participation": participation_metrics(collected.core_prices, config.participation),
        "style": roc35_metrics(
            collected.core_prices,
            value_ticker=config.style.value_ticker,
            growth_ticker=config.style.growth_ticker,
            lookback_sessions=config.style.lookback_sessions,
        ),
        "breadth": _breadth(config, collected),
        "sectors": sector_metrics(collected.core_prices, config.sectors, benchmark="SPY"),
        "semiconductorPulse": semiconductor_pulse(
            collected.core_prices,
            ticker=config.cycle.semiconductor_ticker,
            benchmark=config.cycle.benchmark_ticker,
        ),
        "mega7": mega7_metrics(collected.core_prices, config.mega7),
        "risk": risk_metrics(collected.core_prices["SPY"], collected.vix),
        "treasuryCurve": treasury_curve_metrics(collected.treasury),
        "macro": (
            macro_metrics(collected.fred_series, config.fred_series)
            if collected.fred_series is not None
            else {}
        ),
        "financialStress": (
            financial_stress_metrics(collected.ofr) if collected.ofr is not None else {}
        ),
        "timeSeries": build_time_series(collected, config.mega7),
    }
    return {
        "schemaVersion": "2.0",
        "methodologyVersion": config.methodology_version,
        "asOf": collected.market_as_of.isoformat(),
        "qualityStatus": "DEGRADED" if failed else "APPROVED",
        "producerCommit": producer_commit,
        "sources": [_source_entry(config, status) for status in collected.source_status],
        "data": data,
        "signals": build_indicator_snapshot(data, as_of=collected.market_as_of),
    }
