"""Local point-in-time store for future replay and backtest research."""

import json
import sqlite3
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker

_CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "research-observation.schema.json"
_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS research_observation (
  release_id TEXT PRIMARY KEY,
  core_digest TEXT NOT NULL UNIQUE,
  as_of TEXT NOT NULL,
  available_at TEXT NOT NULL,
  methodology_version TEXT NOT NULL,
  quality_status TEXT NOT NULL,
  payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
  ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
) STRICT;
CREATE INDEX IF NOT EXISTS research_observation_pit_idx
  ON research_observation(as_of, available_at);
CREATE TABLE IF NOT EXISTS signal_feature (
  release_id TEXT NOT NULL REFERENCES research_observation(release_id),
  feature_id TEXT NOT NULL,
  value_json TEXT NOT NULL CHECK (json_valid(value_json)),
  normalized_score REAL,
  confidence REAL,
  weight REAL,
  contribution REAL,
  PRIMARY KEY (release_id, feature_id)
) STRICT;
"""


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return cast(Mapping[str, object], value)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _source_availability(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("core.sources must be an array")
    result = []
    for index, item in enumerate(value):
        source = _mapping(item, f"core.sources[{index}]")
        result.append(
            {
                "sourceId": _string(source.get("sourceId"), "sourceId"),
                "status": _string(source.get("status"), "status"),
                "sourceAsOf": source.get("asOf"),
            }
        )
    return result


def build_research_observation(envelope: Mapping[str, object]) -> dict[str, object]:
    core = _mapping(envelope.get("core"), "core")
    digest = _string(envelope.get("coreDigest"), "coreDigest")
    release_id = _string(envelope.get("releaseId"), "releaseId")
    if release_id != f"mr_{digest}":
        raise ValueError("releaseId does not match coreDigest")
    observation = {
        "schemaVersion": "1.0",
        "releaseId": release_id,
        "coreDigest": digest,
        "asOf": _string(core.get("asOf"), "core.asOf"),
        "availableAt": _string(envelope.get("generatedAt"), "generatedAt"),
        "methodologyVersion": _string(core.get("methodologyVersion"), "core.methodologyVersion"),
        "qualityStatus": _string(core.get("qualityStatus"), "core.qualityStatus"),
        "sourceAvailability": _source_availability(core.get("sources")),
        "signals": dict(_mapping(core.get("signals"), "core.signals")),
        "pitPolicy": {
            "availableAtBasis": "market-release-generated-at",
            "revisions": "append-only",
            "macroVintage": "captured-as-received",
        },
    }
    schema = json.loads(_CONTRACT.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(observation)
    return observation


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _scored_signals(signals: Mapping[str, object]) -> Iterator[Mapping[str, object]]:
    observations = _mapping(signals.get("observations"), "signals.observations")
    for value in observations.values():
        if isinstance(value, dict):
            yield cast(Mapping[str, object], value)
    for field in ("riskWindow", "marketSignal"):
        yield _mapping(signals.get(field), f"signals.{field}")


def _feature_rows(signals: Mapping[str, object]) -> Iterator[tuple[object, ...]]:
    for signal in _scored_signals(signals):
        signal_id = signal.get("indicatorId") or signal.get("signalId")
        if not isinstance(signal_id, str):
            continue
        score = _number(signal.get("score"))
        if score is None:
            score = _number(signal.get("riskScore"))
        confidence = _number(signal.get("confidence"))
        if score is not None:
            yield (f"{signal_id}.score", score, score, confidence, None, None)
        components = signal.get("components")
        if not isinstance(components, list):
            continue
        for item in components:
            component = _mapping(item, f"{signal_id}.components")
            component_id = _string(component.get("componentId"), "componentId")
            yield (
                f"{signal_id}.{component_id}",
                component.get("value"),
                _number(component.get("score")),
                confidence,
                _number(component.get("weight")),
                _number(component.get("contribution")),
            )


class ResearchStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(_SCHEMA_SQL)
        return connection

    def ingest(self, envelope: Mapping[str, object]) -> bool:
        observation = build_research_observation(envelope)
        release_id = str(observation["releaseId"])
        with self._connect() as connection:
            current = connection.execute(
                "SELECT core_digest FROM research_observation WHERE release_id = ?",
                (release_id,),
            ).fetchone()
            if current is not None and current[0] != observation["coreDigest"]:
                raise ValueError("research observation digest conflict")
            inserted = current is None
            connection.execute(
                """INSERT OR IGNORE INTO research_observation
                (release_id, core_digest, as_of, available_at, methodology_version,
                 quality_status, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    release_id,
                    observation["coreDigest"],
                    observation["asOf"],
                    observation["availableAt"],
                    observation["methodologyVersion"],
                    observation["qualityStatus"],
                    json.dumps(observation, ensure_ascii=False, separators=(",", ":")),
                ),
            )
            signals = _mapping(observation["signals"], "signals")
            self._insert_features(connection, release_id, signals)
        return inserted

    @staticmethod
    def _insert_features(
        connection: sqlite3.Connection,
        release_id: str,
        signals: Mapping[str, object],
    ) -> None:
        rows = [
            (release_id, feature_id, json.dumps(value), score, confidence, weight, contribution)
            for feature_id, value, score, confidence, weight, contribution in _feature_rows(signals)
        ]
        connection.executemany(
            """INSERT OR IGNORE INTO signal_feature
            (release_id, feature_id, value_json, normalized_score, confidence, weight,
             contribution) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )

    def status(self) -> dict[str, object]:
        with self._connect() as connection:
            observation_count = connection.execute(
                "SELECT COUNT(*) FROM research_observation"
            ).fetchone()[0]
            feature_count = connection.execute("SELECT COUNT(*) FROM signal_feature").fetchone()[0]
            latest = connection.execute(
                """SELECT as_of, available_at FROM research_observation
                ORDER BY available_at DESC LIMIT 1"""
            ).fetchone()
        return {
            "observationCount": observation_count,
            "featureCount": feature_count,
            "latestAsOf": latest[0] if latest else None,
            "latestAvailableAt": latest[1] if latest else None,
        }
