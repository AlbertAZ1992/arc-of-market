from datetime import date
from pathlib import Path

import pandas as pd

from arc_market.config import load_market_config
from arc_market.models import (
    BreadthInput,
    CollectedMarketData,
    OfrSnapshot,
    SourceStatus,
    TreasurySnapshot,
    UniverseSnapshot,
    VixSnapshot,
)
from arc_market.pipeline import build_release_core


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


def fred_series() -> dict[str, pd.Series]:
    monthly_index = pd.date_range(end="2026-07-01", periods=18, freq="MS")
    daily_index = pd.bdate_range(end="2026-08-28", periods=10)
    return {
        "SOFR": pd.Series(range(10), index=daily_index, dtype="float64"),
        "EFFR": pd.Series(range(10), index=daily_index, dtype="float64"),
        "RRPONTSYD": pd.Series(range(10), index=daily_index, dtype="float64"),
        "WALCL": pd.Series([7_000_000 + index for index in range(10)], index=daily_index),
        "DGS2": pd.Series(range(10), index=daily_index, dtype="float64"),
        "DGS10": pd.Series(range(10), index=daily_index, dtype="float64"),
        "DFII10": pd.Series(range(10), index=daily_index, dtype="float64"),
        "T10Y2Y": pd.Series(range(10), index=daily_index, dtype="float64"),
        "CPIAUCSL": pd.Series(range(100, 118), index=monthly_index, dtype="float64"),
        "CPILFESL": pd.Series(range(100, 118), index=monthly_index, dtype="float64"),
        "PCEPILFE": pd.Series(range(100, 118), index=monthly_index, dtype="float64"),
        "UNRATE": pd.Series(range(18), index=monthly_index, dtype="float64"),
        "PAYEMS": pd.Series(range(100, 118), index=monthly_index, dtype="float64"),
    }


def test_build_release_core_should_cover_launch_modules_with_derived_history() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))
    core_prices = price_frame(config.core_symbols)
    members = ("AAA", "BBB")
    breadth_prices = price_frame(members, periods=220)
    universe = UniverseSnapshot(members, date(2026, 8, 29), "wikipedia")
    collected = CollectedMarketData(
        market_as_of=date(2026, 8, 28),
        core_prices=core_prices,
        breadth={"sp500": BreadthInput(universe, breadth_prices)},
        fred_series=fred_series(),
        vix=VixSnapshot(date(2026, 8, 28), 18.4, date(2026, 8, 27), 17.2),
        ofr=OfrSnapshot(
            date(2026, 8, 28),
            0.5,
            {"credit": 0.1},
            {"unitedStates": 0.3},
        ),
        source_status=(SourceStatus("yahoo-finance", "APPROVED", "2026-08-28"),),
        treasury=TreasurySnapshot(date(2026, 8, 28), 4.2, 4.7, 3.0, 1.0, 7.0),
    )

    core = build_release_core(config, collected, producer_commit="a" * 40)

    assert core["qualityStatus"] == "APPROVED"
    assert set(core["data"]) == {
        "marketOverview",
        "marketHistory",
        "trendSnapshot",
        "coreRotationInputs",
        "participation",
        "style",
        "breadth",
        "sectors",
        "semiconductorPulse",
        "mega7",
        "risk",
        "treasuryCurve",
        "macro",
        "financialStress",
        "timeSeries",
    }
    assert len(core["data"]["marketOverview"]) == 4
    history = core["data"]["marketHistory"]
    assert len(history) == 4
    assert history[0]["proxyTicker"] == "SPY"
    assert history[0]["basis"] == "cumulative_return_pct"
    assert len(history[0]["points"]) == 252
    assert history[0]["points"][0]["value"] == 0.0
    assert core["data"]["style"]["indicatorId"] == "roc35"
    assert len(core["data"]["sectors"]) == 11
    assert len(core["data"]["mega7"]["members"]) == 7
    assert core["data"]["risk"]["vixRegime"] == "neutral"
    assert core["data"]["risk"]["vixChange1dPct"] > 0
    assert core["data"]["treasuryCurve"]["treasury10yChange3dBp"] == 7.0
    assert set(core["signals"]["observations"]) == {
        "trend",
        "participation",
        "style",
        "cycle",
    }
    assert core["signals"]["observations"]["style"]["engineVersion"] == "1.0.0"
    assert core["signals"]["observations"]["trend"]["engineVersion"] == "2.0.0"
    assert "dates" not in str(core)


def test_build_release_core_should_mark_optional_source_failure_degraded() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))
    collected = CollectedMarketData(
        market_as_of=date(2026, 8, 28),
        core_prices=price_frame(config.core_symbols),
        breadth={},
        fred_series=None,
        vix=None,
        ofr=None,
        source_status=(
            SourceStatus("yahoo-finance", "APPROVED", "2026-08-28"),
            SourceStatus("fred", "FAILED", None, "upstream unavailable"),
        ),
    )

    core = build_release_core(config, collected, producer_commit="b" * 40)

    assert core["qualityStatus"] == "DEGRADED"
    assert core["data"]["breadth"] == []
    assert core["data"]["macro"] == {}
    assert core["data"]["risk"]["vixValue"] is None
    assert core["signals"]["riskWindow"]["state"] == "UNAVAILABLE"
