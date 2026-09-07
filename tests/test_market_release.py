import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from arc_market.indicators import build_indicator_snapshot
from arc_market.release import MarketReleasePublisher


def release_core() -> dict[str, object]:
    data: dict[str, object] = {
        "marketOverview": [],
        "trendSnapshot": [],
        "participation": [],
        "style": {
            "indicatorId": "roc35",
            "engineVersion": "1.0.0",
            "valueTicker": "VTV",
            "growthTicker": "QQQ",
            "asOf": "2026-08-28",
            "comparisonAsOf": "2026-07-10",
            "value": 4.08,
            "previousValue": 3.46,
            "change1dPp": 0.62,
            "ratio": 0.31446,
            "ratioChange1dPct": 0.58,
            "direction": "RISING",
            "zeroCross": "NONE",
            "distanceFromZeroPp": 4.08,
            "recent": [],
            "evidence": {
                "current": {
                    "asOf": "2026-08-28",
                    "valueAdjustedClose": 225.29,
                    "growthAdjustedClose": 716.43,
                },
                "comparison": {
                    "asOf": "2026-07-10",
                    "valueAdjustedClose": 219.2,
                    "growthAdjustedClose": 725.51,
                },
            },
        },
        "breadth": [],
        "sectors": [],
        "semiconductorPulse": {
            "ticker": "SMH",
            "benchmarkTicker": "QQQ",
            "asOf": "2026-08-28",
            "return1d": -1.0,
            "return1w": 1.0,
            "return1m": 2.0,
            "relativeReturn1d": -0.5,
            "relativeReturn1w": 0.2,
            "relativeReturn1m": 0.5,
        },
        "mega7": {
            "basketVersion": "mega7-2026-01",
            "members": [],
            "equalWeight": {},
        },
        "risk": {
            "asOf": "2026-08-28",
            "realizedVol20d": 12.3,
            "realizedVol60d": 13.4,
            "currentDrawdown": -1.2,
            "riskState": "calm",
            "vixValue": None,
            "vixAsOf": None,
            "vixPreviousValue": None,
            "vixPreviousAsOf": None,
            "vixChange1dPct": None,
            "vixRegime": None,
        },
        "treasuryCurve": {},
        "macro": {},
        "financialStress": {},
    }
    return {
        "schemaVersion": "2.0",
        "methodologyVersion": "2.1.0",
        "asOf": "2026-08-28",
        "qualityStatus": "APPROVED",
        "producerCommit": "a" * 40,
        "sources": [],
        "data": data,
        "signals": build_indicator_snapshot(data, as_of=date(2026, 8, 28)),
    }


def test_publisher_should_write_immutable_release_latest_and_ledger(tmp_path: Path) -> None:
    publisher = MarketReleasePublisher(tmp_path)
    generated_at = datetime(2026, 8, 29, 1, 0, tzinfo=UTC)

    first = publisher.publish(release_core(), generated_at=generated_at)
    second = publisher.publish(release_core(), generated_at=generated_at + timedelta(hours=1))

    assert first.release_id == second.release_id
    assert first.path == second.path
    assert first.path.exists()
    latest = json.loads((tmp_path / "market/latest.json").read_text(encoding="utf-8"))
    assert latest["releaseId"] == first.release_id
    assert latest["generatedAt"] == "2026-08-29T01:00:00Z"
    ledger = (tmp_path / "market/ledger.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(ledger) == 1


def test_publisher_should_reject_raw_market_history_fields(tmp_path: Path) -> None:
    publisher = MarketReleasePublisher(tmp_path)
    core = release_core()
    core["data"] = {**core["data"], "dates": ["2026-08-28"]}  # type: ignore[dict-item]

    try:
        publisher.publish(
            core,
            generated_at=datetime(2026, 8, 29, tzinfo=UTC),
        )
    except ValueError as error:
        assert "raw market history" in str(error)
    else:
        raise AssertionError("raw market history was accepted")


def test_publisher_should_reject_unknown_nested_fields(tmp_path: Path) -> None:
    publisher = MarketReleasePublisher(tmp_path)
    core = release_core()
    core["data"]["risk"] = {"unknownMetric": 1}  # type: ignore[index]

    try:
        publisher.publish(
            core,
            generated_at=datetime(2026, 8, 29, tzinfo=UTC),
        )
    except ValueError as error:
        assert "contract violation" in str(error)
    else:
        raise AssertionError("unknown nested Market Release field was accepted")


def test_publisher_should_reject_ice_bofa_public_source(tmp_path: Path) -> None:
    publisher = MarketReleasePublisher(tmp_path)
    core = release_core()
    core["sources"] = [
        {
            "sourceId": "ice-data-indices",
            "status": "APPROVED",
            "asOf": "2026-08-28",
            "message": None,
            "url": "https://fred.stlouisfed.org/series/BAMLH0A0HYM2",
            "publishPolicy": "derived-only",
            "attribution": "ICE BofA",
        }
    ]

    try:
        publisher.publish(core, generated_at=datetime(2026, 8, 29, tzinfo=UTC))
    except ValueError as error:
        assert "ICE/BofA" in str(error)
    else:
        raise AssertionError("ICE/BofA source was accepted for public release")


def test_publisher_should_reject_ice_bofa_time_series_source(tmp_path: Path) -> None:
    publisher = MarketReleasePublisher(tmp_path)
    core = release_core()
    core["data"]["timeSeries"] = [  # type: ignore[index]
        {
            "seriesId": "equity-allocation",
            "sourceIds": ["fred", "ice-data-indices"],
            "cadence": "quarterly",
            "basis": "allocation_pct",
            "startAsOf": "2026-03-31",
            "endAsOf": "2026-06-30",
            "points": [
                {"asOf": "2026-03-31", "value": 42.0},
                {"asOf": "2026-06-30", "value": 43.0},
            ],
        }
    ]

    try:
        publisher.publish(core, generated_at=datetime(2026, 8, 29, tzinfo=UTC))
    except ValueError as error:
        assert "ICE/BofA" in str(error)
    else:
        raise AssertionError("ICE/BofA time-series source was accepted for public release")


def test_publisher_should_accept_reviewed_macro_source_series_list(tmp_path: Path) -> None:
    publisher = MarketReleasePublisher(tmp_path)
    core = release_core()
    core["data"]["macro"] = {  # type: ignore[index]
        "breakeven10y": {
            "value": 2.1,
            "asOf": "2026-08-28",
            "unit": "percentage_points",
            "sourceSeries": ["DGS10", "DFII10"],
            "vintage": "latest revised; not point-in-time safe",
        }
    }

    receipt = publisher.publish(core, generated_at=datetime(2026, 8, 29, tzinfo=UTC))

    assert receipt.path.exists()


def test_publisher_should_not_replace_approved_latest_with_same_day_degraded(
    tmp_path: Path,
) -> None:
    publisher = MarketReleasePublisher(tmp_path)
    generated_at = datetime(2026, 8, 29, 1, 0, tzinfo=UTC)
    approved = publisher.publish(release_core(), generated_at=generated_at)
    degraded_core = release_core()
    degraded_core["qualityStatus"] = "DEGRADED"
    degraded_core["sources"] = [
        {
            "sourceId": "fred",
            "status": "FAILED",
            "asOf": None,
            "message": "FRED request failed",
            "url": None,
            "publishPolicy": None,
            "attribution": None,
        }
    ]

    result = publisher.publish(degraded_core, generated_at=generated_at + timedelta(hours=1))

    assert result.release_id == approved.release_id
    assert len((tmp_path / "market/ledger.jsonl").read_text().splitlines()) == 1
