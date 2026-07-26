import json
from pathlib import Path

from scripts.dataset_rights import validate_registry

ROOT = Path(__file__).resolve().parent.parent


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_repository_dataset_registry_is_complete() -> None:
    assert validate_registry() == []


def test_public_fred_series_have_no_copyright_marker() -> None:
    registry = json.loads(
        (ROOT / "config" / "fred-series-registry.json").read_text(encoding="utf-8")
    )
    public_series = [row for row in registry["series"] if row["public"]]
    internal_series = {row["id"]: row for row in registry["series"] if not row["public"]}

    assert len(public_series) == 22
    assert all(not row["copyright_note"] for row in public_series)
    assert set(internal_series) == {"BAMLH0A0HYM2", "BAMLC0A0CM"}
    assert all(row["copyright_note"] for row in internal_series.values())


def test_registry_rejects_unregistered_file(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    write_json(data_dir / "unexpected.json", {})

    issues = validate_registry(data_dir=data_dir)

    assert "unregistered data file unexpected.json" in issues


def test_registry_rejects_public_dataset_with_internal_source(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    write_json(data_dir / "sample.json", {})
    registry = tmp_path / "datasets.json"
    write_json(
        registry,
        {
            "schema_version": 1,
            "default_access": "deny",
            "groups": [
                {
                    "id": "sample",
                    "files": ["sample.json"],
                    "source_ids": ["private-source"],
                    "access": {"public": True, "subscriber": False},
                    "derived_output": "allowed",
                    "status": "approved",
                    "approval_reference": "review-1",
                }
            ],
        },
    )
    sources = tmp_path / "sources.json"
    write_json(
        sources,
        {"sources": [{"id": "private-source", "public_status": "internal-only"}]},
    )
    public_policy = tmp_path / "public.json"
    write_json(
        public_policy,
        {
            "schema_version": 1,
            "default": "deny",
            "files": {"sample.json": {"public": True}},
        },
    )
    subscriber_policy = tmp_path / "subscriber.json"
    write_json(
        subscriber_policy,
        {"schema_version": 1, "default": "deny", "files": {}},
    )

    issues = validate_registry(
        data_dir=data_dir,
        registry_path=registry,
        source_path=sources,
        policies={"public": public_policy, "subscriber": subscriber_policy},
    )

    assert "group sample uses non-public source private-source" in issues


def test_registry_accepts_recorded_product_owner_chart_decision(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    write_json(data_dir / "sample.json", {})
    registry = tmp_path / "datasets.json"
    write_json(
        registry,
        {
            "schema_version": 1,
            "default_access": "deny",
            "groups": [
                {
                    "id": "sample",
                    "files": ["sample.json"],
                    "source_ids": ["research-source"],
                    "access": {"public": True, "subscriber": False},
                    "derived_output": "allowed-with-attribution",
                    "status": "approved-for-public-chart-display",
                    "approval_reference": (
                        "Product owner data-display decision 2026-07-26"
                    ),
                }
            ],
        },
    )
    sources = tmp_path / "sources.json"
    write_json(
        sources,
        {"sources": [{"id": "research-source", "public_status": "internal-only"}]},
    )
    public_policy = tmp_path / "public.json"
    write_json(
        public_policy,
        {
            "schema_version": 1,
            "default": "deny",
            "files": {"sample.json": {"public": True}},
        },
    )
    subscriber_policy = tmp_path / "subscriber.json"
    write_json(
        subscriber_policy,
        {"schema_version": 1, "default": "deny", "files": {}},
    )

    issues = validate_registry(
        data_dir=data_dir,
        registry_path=registry,
        source_path=sources,
        policies={"public": public_policy, "subscriber": subscriber_policy},
    )

    assert issues == []
