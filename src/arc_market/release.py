"""Content-addressed publication of one compact Market Release."""

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

_CORE_FIELDS = {
    "schemaVersion",
    "methodologyVersion",
    "asOf",
    "qualityStatus",
    "producerCommit",
    "sources",
    "data",
    "signals",
}
_RAW_HISTORY_FIELDS = {
    "dates",
    "adjustedClose",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "ohlcv",
    "prices",
}
_FORBIDDEN_PUBLIC_SOURCE_IDS = {"ice-data-indices"}
_FORBIDDEN_PUBLIC_SERIES_IDS = {"BAMLH0A0HYM2"}
_CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "market-release.schema.json"


@dataclass(frozen=True)
class MarketReleaseReceipt:
    release_id: str
    path: Path
    latest_path: Path


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _reject_non_finite(value: object, path: str = "core") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path} contains a non-finite number")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_non_finite(item, f"{path}.{key}")
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _reject_non_finite(item, f"{path}[{index}]")


def _reject_raw_history(value: object, path: str = "core") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _RAW_HISTORY_FIELDS:
                raise ValueError(f"raw market history field is forbidden: {path}.{key}")
            _reject_raw_history(item, f"{path}.{key}")
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            _reject_raw_history(item, f"{path}[{index}]")


def _contains_identifier(value: object, identifiers: set[str]) -> bool:
    if isinstance(value, str):
        return value in identifiers
    if isinstance(value, list):
        return any(isinstance(item, str) and item in identifiers for item in value)
    return False


def _reject_forbidden_sources(sources: object) -> None:
    if isinstance(sources, list):
        for source in sources:
            source_id = source.get("sourceId") if isinstance(source, dict) else None
            if _contains_identifier(source_id, _FORBIDDEN_PUBLIC_SOURCE_IDS):
                raise ValueError("ICE/BofA data is forbidden in a public Market Release")


def _reject_forbidden_time_series(data: object) -> None:
    time_series = data.get("timeSeries") if isinstance(data, dict) else None
    if isinstance(time_series, list):
        for series in time_series:
            source_ids = series.get("sourceIds") if isinstance(series, dict) else None
            if _contains_identifier(source_ids, _FORBIDDEN_PUBLIC_SOURCE_IDS):
                raise ValueError("ICE/BofA data is forbidden in a public Market Release")


def _reject_forbidden_macro(data: object) -> None:
    macro = data.get("macro") if isinstance(data, dict) else None
    if isinstance(macro, dict):
        for metric in macro.values():
            source_series = metric.get("sourceSeries") if isinstance(metric, dict) else None
            if _contains_identifier(source_series, _FORBIDDEN_PUBLIC_SERIES_IDS):
                raise ValueError("ICE/BofA data is forbidden in a public Market Release")


def _reject_forbidden_public_data(core: dict[str, object]) -> None:
    _reject_forbidden_sources(core.get("sources"))
    _reject_forbidden_time_series(core.get("data"))
    _reject_forbidden_macro(core.get("data"))


def validate_release_core(core: dict[str, object]) -> None:
    if set(core) != _CORE_FIELDS:
        raise ValueError("Market Release core fields are invalid")
    if core["schemaVersion"] != "2.0":
        raise ValueError("Market Release schemaVersion must be 2.0")
    if core["qualityStatus"] not in {"APPROVED", "DEGRADED"}:
        raise ValueError("Market Release qualityStatus is invalid")
    if not isinstance(core["sources"], list) or not isinstance(core["data"], dict):
        raise ValueError("Market Release sources and data types are invalid")
    _reject_forbidden_public_data(core)
    _reject_non_finite(core)
    _reject_raw_history(core)
    try:
        schema = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(core)
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        raise ValueError(f"Market Release contract is unavailable: {error}") from error
    except ValidationError as error:
        location = ".".join(str(item) for item in error.absolute_path) or "core"
        raise ValueError(
            f"Market Release contract violation at {location}: {error.message}"
        ) from error


def _write_json_atomic(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(value, handle, ensure_ascii=False, allow_nan=False, indent=2)
            handle.write("\n")
            temporary = Path(handle.name)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class MarketReleasePublisher:
    def __init__(self, releases_root: Path) -> None:
        self._root = releases_root.resolve() / "market"

    def _ledger_entry(
        self, release_id: str, core: dict[str, object], path: Path
    ) -> dict[str, object]:
        return {
            "releaseId": release_id,
            "asOf": core["asOf"],
            "coreDigest": release_id.removeprefix("mr_"),
            "path": path.relative_to(self._root.parent).as_posix(),
        }

    def _append_ledger(self, entry: dict[str, object]) -> None:
        path = self._root / "ledger.jsonl"
        existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        rows = [json.loads(line) for line in existing]
        if entry in rows:
            return
        if any(row.get("releaseId") == entry["releaseId"] for row in rows):
            raise ValueError(f"Market Release ledger conflict: {entry['releaseId']}")
        encoded = "\n".join([*existing, json.dumps(entry, separators=(",", ":"))]) + "\n"
        _write_text_atomic(path, encoded)

    def publish(
        self,
        core: dict[str, object],
        *,
        generated_at: datetime,
    ) -> MarketReleaseReceipt:
        validate_release_core(core)
        latest_path = self._root / "latest.json"
        if latest_path.exists():
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            latest_core = latest.get("core", {})
            if (
                isinstance(latest_core, dict)
                and latest_core.get("asOf") == core["asOf"]
                and latest_core.get("qualityStatus") == "APPROVED"
                and core["qualityStatus"] == "DEGRADED"
            ):
                latest_id = str(latest["releaseId"])
                latest_methodology = str(latest_core["methodologyVersion"])
                latest_release = (
                    self._root / latest_methodology / str(latest_core["asOf"]) / f"{latest_id}.json"
                )
                return MarketReleaseReceipt(latest_id, latest_release, latest_path)
        core_digest = hashlib.sha256(_canonical_bytes(core)).hexdigest()
        release_id = f"mr_{core_digest}"
        methodology = str(core["methodologyVersion"])
        as_of = str(core["asOf"])
        path = self._root / methodology / as_of / f"{release_id}.json"
        envelope: dict[str, object] = {
            "releaseId": release_id,
            "coreDigest": core_digest,
            "generatedAt": generated_at.isoformat().replace("+00:00", "Z"),
            "core": core,
        }
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if (
                existing.get("releaseId") != release_id
                or existing.get("coreDigest") != core_digest
                or existing.get("core") != core
            ):
                raise ValueError(f"immutable Market Release conflict: {release_id}")
            envelope = existing
        else:
            _write_json_atomic(path, envelope)
        self._append_ledger(self._ledger_entry(release_id, core, path))
        _write_json_atomic(latest_path, envelope)
        return MarketReleaseReceipt(release_id, path, latest_path)
