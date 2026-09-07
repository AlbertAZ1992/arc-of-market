from datetime import date

import pandas as pd

from arc_market.calculations import semiconductor_pulse, trend_snapshot
from arc_market.indicators import build_indicator_snapshot


def price_frame() -> pd.DataFrame:
    index = pd.bdate_range(end="2026-08-28", periods=270)
    return pd.DataFrame(
        {
            "SPY": [100 + step for step in range(len(index))],
            "QQQ": [120 + step * 1.2 for step in range(len(index))],
            "SMH": [80 + step * 1.4 for step in range(len(index))],
        },
        index=index,
        dtype="float64",
    )


def broad_inputs() -> dict[str, object]:
    return {
        "marketOverview": [
            {
                "proxyTicker": ticker,
                "return1m": monthly_return,
                "aboveMa50": True,
                "aboveMa200": True,
                "realizedVol20d": volatility,
            }
            for ticker, monthly_return, volatility in (
                ("SPY", 4.0, 12.0),
                ("QQQ", 5.0, 16.0),
                ("IWM", 6.0, 18.0),
            )
        ],
        "trendSnapshot": [
            {
                "ticker": ticker,
                "aboveMa20": True,
                "aboveMa50": True,
            }
            for ticker in ("SPY", "QQQ")
        ],
        "participation": [
            {
                "pairId": pair_id,
                "relativeReturn1m": 2.0,
                "ratioAboveMa50": True,
                "participationState": "broadening",
            }
            for pair_id in ("sp500_equal_weight", "nasdaq100_equal_weight")
        ],
        "breadth": [
            {
                "indexId": index_id,
                "pctAboveMa50": 70.0,
                "pctAboveMa200": 65.0,
                "breadthState": "strong",
            }
            for index_id in ("sp500", "nasdaq100")
        ],
        "style": {"value": 2.0, "direction": "RISING"},
        "semiconductorPulse": {
            "relativeReturn1d": 0.2,
            "relativeReturn1w": 0.5,
            "relativeReturn1m": 1.0,
        },
        "sectors": [
            {"ticker": ticker, "relative1m": relative, "return1m": relative + 2.0}
            for ticker, relative in (
                ("XLY", 2.0),
                ("XLI", 1.5),
                ("XLF", 1.0),
                ("XLP", -1.0),
                ("XLU", -1.5),
                ("XLV", -0.5),
            )
        ],
        "risk": {
            "vixValue": 14.0,
            "vixChange1dPct": -2.0,
            "realizedVol20d": 12.0,
            "realizedVol60d": 15.0,
            "currentDrawdown": -2.0,
            "vixRegime": "low",
        },
        "treasuryCurve": {"treasury10yChange3dBp": 5.0},
        "financialStress": {"value": -0.5},
    }


def test_trend_snapshot_should_publish_short_moving_averages_and_distances() -> None:
    result = trend_snapshot(price_frame(), ("SPY", "QQQ"))

    assert [row["ticker"] for row in result] == ["SPY", "QQQ"]
    assert result[1]["asOf"] == "2026-08-28"
    assert result[1]["priceBasis"] == "adjusted_close"
    assert result[1]["ma5"] > result[1]["ma10"] > result[1]["ma20"] > result[1]["ma50"]
    assert result[1]["aboveMa20"] is True
    assert result[1]["aboveMa50"] is True
    assert result[1]["distanceMa20Pct"] > 0


def test_semiconductor_pulse_should_compare_smh_with_qqq() -> None:
    result = semiconductor_pulse(price_frame(), ticker="SMH", benchmark="QQQ")

    assert result["ticker"] == "SMH"
    assert result["benchmarkTicker"] == "QQQ"
    assert result["asOf"] == "2026-08-28"
    assert result["relativeReturn1w"] > 0
    assert result["relativeReturn1m"] > 0


def test_indicator_snapshot_should_build_four_observations_risk_gate_and_signal() -> None:
    result = build_indicator_snapshot(broad_inputs(), as_of=date(2026, 8, 28))

    assert set(result["observations"]) == {"trend", "participation", "style", "cycle"}
    assert result["observations"]["trend"]["state"] == "BULLISH"
    assert result["observations"]["participation"]["state"] == "BROAD"
    assert result["observations"]["style"]["state"] == "VALUE_LEADING"
    assert result["observations"]["cycle"]["state"] == "LEADING"
    assert result["riskWindow"]["state"] == "OPEN"
    assert result["marketSignal"]["state"] == "RISK_ON"


def test_low_vix_with_weak_tech_and_rising_rates_should_be_watch_not_defensive() -> None:
    data = broad_inputs()
    data["trendSnapshot"] = [
        {"ticker": "SPY", "aboveMa20": True, "aboveMa50": True},
        {"ticker": "QQQ", "aboveMa20": False, "aboveMa50": True},
    ]
    data["participation"] = [
        {
            "pairId": "sp500_equal_weight",
            "relativeReturn1m": 0.0,
            "ratioAboveMa50": True,
            "participationState": "mixed",
        },
        {
            "pairId": "nasdaq100_equal_weight",
            "relativeReturn1m": -2.0,
            "ratioAboveMa50": False,
            "participationState": "narrowing",
        },
    ]
    data["breadth"] = [
        {
            "indexId": "sp500",
            "pctAboveMa50": 55.0,
            "pctAboveMa200": 60.0,
            "breadthState": "mixed",
        },
        {
            "indexId": "nasdaq100",
            "pctAboveMa50": 40.0,
            "pctAboveMa200": 45.0,
            "breadthState": "weak",
        },
    ]
    data["semiconductorPulse"] = {
        "relativeReturn1d": -2.8,
        "relativeReturn1w": -0.5,
        "relativeReturn1m": -1.0,
    }
    data["treasuryCurve"] = {"treasury10yChange3dBp": 12.0}
    data["sectors"] = [
        {"ticker": ticker, "relative1m": relative, "return1m": relative}
        for ticker, relative in (
            ("XLY", -2.0),
            ("XLI", -1.5),
            ("XLF", -1.0),
            ("XLP", 1.0),
            ("XLU", 1.5),
            ("XLV", 0.5),
        )
    ]

    result = build_indicator_snapshot(data, as_of=date(2026, 8, 28))

    assert result["observations"]["trend"]["state"] == "BULLISH"
    assert result["observations"]["cycle"]["state"] == "MIXED"
    assert result["riskWindow"]["state"] == "OPEN"
    assert result["marketSignal"]["state"] == "WATCH"
