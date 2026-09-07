from datetime import date

from arc_market.indicators import build_indicator_snapshot
from arc_market.scores import participation_score


def constructive_inputs() -> dict[str, object]:
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
            {"ticker": ticker, "aboveMa20": True, "aboveMa50": True} for ticker in ("SPY", "QQQ")
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
            "relativeReturn1w": 2.0,
            "relativeReturn1m": 3.0,
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
        "treasuryCurve": {"treasury10yChange3dBp": -3.0},
        "financialStress": {"value": -0.5},
    }


def test_v2_scores_should_publish_transparent_components() -> None:
    result = build_indicator_snapshot(constructive_inputs(), as_of=date(2026, 8, 28))

    observations = result["observations"]
    assert observations["trend"]["engineVersion"] == "2.0.0"
    assert observations["trend"]["score"] >= 65
    assert observations["participation"]["score"] >= 60
    assert observations["cycle"]["score"] >= 60
    assert observations["style"] == {
        "indicatorId": "style",
        "engineVersion": "1.0.0",
        "state": "VALUE_LEADING",
        "roc35": 2.0,
        "direction": "RISING",
    }
    assert observations["trend"]["components"]
    assert result["riskWindow"]["riskScore"] <= 30
    assert result["marketSignal"]["state"] == "RISK_ON"
    assert result["marketSignal"]["styleIncludedInScore"] is False


def test_v2_scores_should_turn_defensive_when_confirmations_deteriorate() -> None:
    data = constructive_inputs()
    data["marketOverview"] = [
        {
            "proxyTicker": ticker,
            "return1m": -8.0,
            "aboveMa50": False,
            "aboveMa200": False,
            "realizedVol20d": 35.0,
        }
        for ticker in ("SPY", "QQQ", "IWM")
    ]
    data["trendSnapshot"] = [
        {"ticker": ticker, "aboveMa20": False, "aboveMa50": False} for ticker in ("SPY", "QQQ")
    ]
    data["participation"] = [
        {
            "pairId": pair_id,
            "relativeReturn1m": -4.0,
            "ratioAboveMa50": False,
            "participationState": "narrowing",
        }
        for pair_id in ("sp500_equal_weight", "nasdaq100_equal_weight")
    ]
    data["breadth"] = [
        {"indexId": index_id, "pctAboveMa50": 25.0, "pctAboveMa200": 30.0}
        for index_id in ("sp500", "nasdaq100")
    ]
    data["semiconductorPulse"] = {
        "relativeReturn1w": -5.0,
        "relativeReturn1m": -8.0,
    }
    data["sectors"] = [
        {"ticker": ticker, "relative1m": relative, "return1m": relative - 2.0}
        for ticker, relative in (
            ("XLY", -4.0),
            ("XLI", -3.0),
            ("XLF", -2.0),
            ("XLP", 2.0),
            ("XLU", 3.0),
            ("XLV", 2.0),
        )
    ]
    data["risk"] = {
        "vixValue": 35.0,
        "vixChange1dPct": 20.0,
        "realizedVol20d": 40.0,
        "realizedVol60d": 20.0,
        "currentDrawdown": -18.0,
        "vixRegime": "stress",
    }
    data["treasuryCurve"] = {"treasury10yChange3dBp": 20.0}
    data["financialStress"] = {"value": 2.5}

    result = build_indicator_snapshot(data, as_of=date(2026, 8, 28))

    assert result["observations"]["trend"]["state"] == "BEARISH"
    assert result["observations"]["participation"]["state"] == "NARROW"
    assert result["observations"]["cycle"]["state"] == "LAGGING"
    assert result["riskWindow"]["state"] == "CLOSED"
    assert result["marketSignal"]["state"] == "DEFENSIVE"


def test_v2_scores_should_map_neutral_cycle_score_to_mixed() -> None:
    data = constructive_inputs()
    data["marketOverview"] = [{**row, "return1m": 4.0} for row in data["marketOverview"]]
    data["semiconductorPulse"] = {"relativeReturn1w": 0.0, "relativeReturn1m": 0.0}
    data["sectors"] = [
        {"ticker": ticker, "relative1m": 0.0, "return1m": 1.0 if index < 3 else -1.0}
        for index, ticker in enumerate(("XLY", "XLI", "XLF", "XLP", "XLU", "XLV"))
    ]

    result = build_indicator_snapshot(data, as_of=date(2026, 8, 28))

    assert result["observations"]["cycle"]["state"] == "MIXED"


def test_v2_scores_should_map_neutral_participation_score_to_mixed() -> None:
    data = {
        "breadth": [
            {"indexId": index_id, "pctAboveMa50": 50.0, "pctAboveMa200": 50.0}
            for index_id in ("sp500", "nasdaq100")
        ],
        "participation": [
            {
                "pairId": pair_id,
                "relativeReturn1m": 0.0,
                "ratioAboveMa50": index == 0,
            }
            for index, pair_id in enumerate(("sp500_equal_weight", "nasdaq100_equal_weight"))
        ],
    }

    assert participation_score(data)["state"] == "MIXED"


def test_v2_scores_should_expose_low_confidence_instead_of_inventing_values() -> None:
    result = build_indicator_snapshot(
        {"style": {"value": 0.0, "direction": "FLAT"}},
        as_of=date(2026, 8, 28),
    )

    assert result["observations"]["trend"]["state"] == "UNAVAILABLE"
    assert result["observations"]["participation"]["state"] == "UNAVAILABLE"
    assert result["riskWindow"]["state"] == "UNAVAILABLE"
    assert result["marketSignal"]["state"] == "UNAVAILABLE"
