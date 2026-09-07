from datetime import date

import pandas as pd

from arc_market.calculations import (
    benchmark_metrics,
    breadth_metrics,
    mega7_metrics,
    roc35_metrics,
    sector_metrics,
    vix_regime,
)


def price_frame(symbols: tuple[str, ...], *, periods: int = 270) -> pd.DataFrame:
    index = pd.bdate_range(end="2026-08-28", periods=periods)
    return pd.DataFrame(
        {
            symbol: [100 + offset + step for step in range(periods)]
            for offset, symbol in enumerate(symbols)
        },
        index=index,
        dtype="float64",
    )


def test_benchmark_metrics_should_publish_only_compact_derived_values() -> None:
    prices = price_frame(("SPY",))

    result = benchmark_metrics(prices["SPY"], "sp500_proxy", "SPY")

    assert result["benchmarkId"] == "sp500_proxy"
    assert result["proxyTicker"] == "SPY"
    assert result["asOf"] == "2026-08-28"
    assert result["return1w"] > 0
    assert result["return1m"] > result["return1w"]
    assert result["aboveMa50"] is True
    assert result["aboveMa200"] is True
    assert result["trendState"] == "uptrend"
    assert "dates" not in result
    assert "adjustedClose" not in result


def test_sector_metrics_should_rank_by_one_month_relative_to_spy() -> None:
    prices = price_frame(("SPY", "XLK", "XLU"))
    prices["XLK"] = [100 + step * 2 for step in range(len(prices))]
    prices["XLU"] = [100 + step * 0.5 for step in range(len(prices))]

    result = sector_metrics(
        prices,
        {"XLK": "信息科技", "XLU": "公用事业"},
        benchmark="SPY",
    )

    assert [item["ticker"] for item in result] == ["XLK", "XLU"]
    assert [item["rank"] for item in result] == [1, 2]
    assert result[0]["relative1m"] > result[1]["relative1m"]
    assert set(result[0]) == {
        "ticker",
        "label",
        "asOf",
        "return1d",
        "return1w",
        "return1m",
        "returnYtd",
        "relative1m",
        "rank",
    }


def test_mega7_metrics_should_publish_equal_weight_period_returns() -> None:
    members = ("AAPL", "MSFT")
    prices = price_frame(("SPY", "QQQ", *members))

    result = mega7_metrics(prices, members)

    assert result["basketVersion"] == "mega7-2026-01"
    assert [item["ticker"] for item in result["members"]] == ["AAPL", "MSFT"]
    assert set(result["equalWeight"]) == {
        "return1d",
        "return1w",
        "return1m",
        "returnYtd",
    }
    assert "prices" not in result


def test_breadth_metrics_should_expose_coverage_and_current_universe_caveat() -> None:
    prices = price_frame(("AAA", "BBB", "CCC"), periods=220)
    prices["CCC"] = prices["CCC"].iloc[-40:].reindex(prices.index)

    result = breadth_metrics(
        "sp500",
        ("AAA", "BBB", "CCC"),
        prices,
        observed_at=date(2026, 8, 29),
        minimum_coverage=0.6,
    )

    assert result["universeCount"] == 3
    assert result["eligibleCountMa50"] == 2
    assert result["eligibleCountMa200"] == 2
    assert result["pctAboveMa50"] == 100.0
    assert result["pctAboveMa200"] == 100.0
    assert result["caveat"] == "current-universe survivorship bias"


def test_vix_regime_should_use_four_simple_bands() -> None:
    assert vix_regime(14.99) == "low"
    assert vix_regime(15.0) == "neutral"
    assert vix_regime(25.0) == "elevated"
    assert vix_regime(35.0) == "stress"


def test_roc35_metrics_should_publish_compact_reproducible_evidence() -> None:
    prices = price_frame(("VTV", "QQQ"), periods=80)
    prices["VTV"] = [100 + step * 1.5 for step in range(len(prices))]

    result = roc35_metrics(
        prices,
        value_ticker="VTV",
        growth_ticker="QQQ",
        lookback_sessions=35,
    )

    assert result["indicatorId"] == "roc35"
    assert result["asOf"] == "2026-08-28"
    assert result["comparisonAsOf"] < result["asOf"]
    assert result["value"] > 0
    assert len(result["recent"]) == 5
    assert set(result["evidence"]) == {"current", "comparison"}
    assert "dates" not in result
