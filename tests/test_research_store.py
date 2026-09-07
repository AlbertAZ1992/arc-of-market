import sqlite3
from pathlib import Path

import pytest

from arc_market.research_store import ResearchStore, build_research_observation


def release_envelope(*, digest: str = "a" * 64) -> dict[str, object]:
    component = {
        "componentId": "spy-short-trend",
        "value": 100.0,
        "score": 100.0,
        "weight": 0.15,
        "contribution": 15.0,
    }
    signals = {
        "asOf": "2026-08-28",
        "observations": {
            "trend": {
                "indicatorId": "trend",
                "score": 82.0,
                "confidence": 1.0,
                "components": [component],
            },
            "participation": {
                "indicatorId": "participation",
                "score": 60.0,
                "confidence": 1.0,
                "components": [],
            },
            "style": {"indicatorId": "style", "roc35": 4.08},
            "cycle": {
                "indicatorId": "cycle",
                "score": 55.0,
                "confidence": 0.8,
                "components": [],
            },
        },
        "riskWindow": {
            "indicatorId": "risk-window",
            "riskScore": 35.0,
            "confidence": 1.0,
            "components": [],
        },
        "marketSignal": {"signalId": "market-regime", "score": 64.0},
    }
    return {
        "releaseId": f"mr_{digest}",
        "coreDigest": digest,
        "generatedAt": "2026-08-29T01:00:00Z",
        "core": {
            "methodologyVersion": "2.1.0",
            "asOf": "2026-08-28",
            "qualityStatus": "APPROVED",
            "sources": [
                {
                    "sourceId": "yahoo-finance",
                    "status": "APPROVED",
                    "asOf": "2026-08-28",
                }
            ],
            "signals": signals,
        },
    }


def test_observation_should_capture_when_data_became_available() -> None:
    observation = build_research_observation(release_envelope())

    assert observation["asOf"] == "2026-08-28"
    assert observation["availableAt"] == "2026-08-29T01:00:00Z"
    assert observation["pitPolicy"] == {
        "availableAtBasis": "market-release-generated-at",
        "revisions": "append-only",
        "macroVintage": "captured-as-received",
    }
    assert "data" not in observation


def test_store_should_ingest_idempotently_and_normalize_signal_features(tmp_path: Path) -> None:
    path = tmp_path / "research.db"
    store = ResearchStore(path)

    assert store.ingest(release_envelope()) is True
    assert store.ingest(release_envelope()) is False

    status = store.status()
    assert status == {
        "observationCount": 1,
        "featureCount": 6,
        "latestAsOf": "2026-08-28",
        "latestAvailableAt": "2026-08-29T01:00:00Z",
    }
    with sqlite3.connect(path) as connection:
        identifiers = {
            row[0]
            for row in connection.execute(
                "SELECT feature_id FROM signal_feature ORDER BY feature_id"
            )
        }
    assert identifiers == {
        "cycle.score",
        "market-regime.score",
        "participation.score",
        "risk-window.score",
        "trend.score",
        "trend.spy-short-trend",
    }


def test_store_should_reject_a_release_id_with_another_digest(tmp_path: Path) -> None:
    store = ResearchStore(tmp_path / "research.db")
    envelope = release_envelope()
    store.ingest(envelope)
    envelope["coreDigest"] = "b" * 64

    with pytest.raises(ValueError, match="releaseId does not match coreDigest"):
        store.ingest(envelope)
