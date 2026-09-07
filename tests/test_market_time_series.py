from datetime import date
from pathlib import Path

import pandas as pd

from arc_market.config import load_market_config
from arc_market.fetchers.cftc import parse_cftc_rows
from arc_market.models import (
    CftcSnapshot,
    CollectedMarketData,
    OfrSnapshot,
    SourceStatus,
    VixSnapshot,
)
from arc_market.time_series import build_time_series


def _prices(symbols: tuple[str, ...]) -> pd.DataFrame:
    index = pd.bdate_range(end="2026-08-28", periods=270)
    return pd.DataFrame(
        {
            symbol: [100 + offset + step for step in range(270)]
            for offset, symbol in enumerate(symbols)
        },
        index=index,
        dtype="float64",
    )


def _fred() -> dict[str, pd.Series]:
    quarter_index = pd.date_range(end="2026-03-31", periods=120, freq="QE")
    observations = {}
    identifiers = (
        "NCBEILQ027S",
        "FBCELLQ027S",
        "BCNSDODNS",
        "CMDEBT",
        "FGSDODNS",
        "SLGSDODNS",
        "WCMITCMFODNS",
    )
    for offset, series_id in enumerate(identifiers):
        observations[series_id] = pd.Series(
            [1_000 + offset * 100 + index * (offset + 1) for index in range(120)],
            index=quarter_index,
            dtype="float64",
        )
    return observations


def test_parse_cftc_rows_should_calculate_vix_position_share() -> None:
    rows = [
        {
            "report_date_as_yyyy_mm_dd": "2026-08-18T00:00:00.000",
            "lev_money_positions_long": "100",
            "lev_money_positions_short": "160",
            "asset_mgr_positions_long": "90",
            "asset_mgr_positions_short": "30",
            "open_interest_all": "1000",
        },
        {
            "report_date_as_yyyy_mm_dd": "2026-08-25T00:00:00.000",
            "lev_money_positions_long": "125",
            "lev_money_positions_short": "175",
            "asset_mgr_positions_long": "80",
            "asset_mgr_positions_short": "40",
            "open_interest_all": "1000",
        },
    ]
    result = parse_cftc_rows(rows, date(2026, 8, 29), minimum_rows=2)
    assert float(result.history.iloc[-1]["leveragedNetPctOi"]) == -5.0
    assert float(result.history.iloc[-1]["assetManagerNetPctOi"]) == 4.0


def test_release_should_publish_only_reviewed_chart_ready_time_series() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))
    prices = _prices(config.core_symbols)
    fsi_history = pd.DataFrame(
        {"fsi": [0.25, 0.5]},
        index=pd.to_datetime(["2026-08-27", "2026-08-28"]),
    )
    cot_index = pd.date_range(end="2026-08-25", periods=156, freq="W-TUE")
    cot_history = pd.DataFrame(
        {"leveragedNetPctOi": [-(index % 20) for index in range(156)]},
        index=cot_index,
        dtype="float64",
    )
    collected = CollectedMarketData(
        market_as_of=date(2026, 8, 28),
        core_prices=prices,
        breadth={},
        fred_series=_fred(),
        vix=VixSnapshot(
            date(2026, 8, 28),
            18.4,
            date(2026, 8, 27),
            17.2,
            prices["SPY"].tail(252).div(25),
        ),
        ofr=OfrSnapshot(date(2026, 8, 28), 0.5, {}, {}, fsi_history),
        source_status=(SourceStatus("yahoo-finance", "APPROVED", "2026-08-28"),),
        cftc=CftcSnapshot(date(2026, 8, 25), cot_history),
    )
    series = {row["seriesId"]: row for row in build_time_series(collected, config.mega7)}
    assert set(series) == {
        "mega7-equal-weight",
        "cyclicals-defensives",
        "financial-stress",
        "cot-vix",
        "equity-allocation",
    }
    assert len(series["mega7-equal-weight"]["points"]) == 252
    assert series["cot-vix"]["basis"] == "net_pct_open_interest"
    assert series["equity-allocation"]["cadence"] == "quarterly"
    assert series["equity-allocation"]["endAsOf"] == "2026-03-31"
    assert "BAMLH0A0HYM2" not in str(series)
    assert "ice-data-indices" not in str(series)
