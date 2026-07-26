import json
import subprocess
from pathlib import Path

from scripts.audit import git_status_entries, validate_data, validate_sp500_changes


def run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_status_includes_untracked_and_deleted_data(tmp_path: Path) -> None:
    run_git(tmp_path, "init", "-b", "main")
    run_git(tmp_path, "config", "user.name", "Test")
    run_git(tmp_path, "config", "user.email", "test@example.com")
    run_git(tmp_path, "config", "commit.gpgsign", "false")

    data = tmp_path / "data"
    data.mkdir()
    tracked = data / "tracked.json"
    tracked.write_text("{}\n", encoding="utf-8")
    run_git(tmp_path, "add", "data/tracked.json")
    run_git(tmp_path, "commit", "-m", "baseline")

    tracked.unlink()
    (data / "new.json").write_text("{}\n", encoding="utf-8")

    entries = git_status_entries(tmp_path)
    by_path = {entry["path"]: entry["status"] for entry in entries}

    assert by_path["data/tracked.json"] == " D"
    assert by_path["data/new.json"] == "??"


def test_quality_validation_detects_duplicate_dates_and_length_mismatch(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "sample.json").write_text(
        '{"dates":["2025-01-01","2025-01-01"],"values":[1]}\n',
        encoding="utf-8",
    )

    issues = validate_data(data, validate_rights=False)
    messages = [issue["issue"] for issue in issues]

    assert "root dates contain duplicates" in messages
    assert "root.values length 1 != dates length 2" in messages


def test_quality_validation_includes_other_profile_failures(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "meta.json").write_text(
        json.dumps(
            {
                "profile_runs": {
                    "daily": {
                        "failures": [
                            {
                                "section": "source yahoo:^GSPC",
                                "error": "latest row has no close",
                                "blocking": False,
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    issues = validate_data(data, validate_rights=False)

    assert issues == [
        {
            "severity": "warning",
            "path": "meta.json",
            "issue": "source yahoo:^GSPC: latest row has no close",
        }
    ]


def test_sp500_changes_requires_unique_sorted_events_and_revision() -> None:
    valid = {
        "meta": {"source": {"revision": {"id": 123, "url": "https://example.test/123"}}},
        "changes": [
            {
                "effective_date": f"{year:04d}-01-01",
                "addition": {"ticker": f"A{year}"},
                "removal": {"ticker": f"R{year}"},
            }
            for year in range(2325, 2025, -1)
        ],
    }

    assert validate_sp500_changes(valid) == []

    valid["changes"].append(valid["changes"][0])
    issues = validate_sp500_changes(valid)

    assert any(issue["issue"] == "invalid or duplicate event grain" for issue in issues)
