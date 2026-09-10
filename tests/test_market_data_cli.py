from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.market_data import last_completed_market_date, write_github_output


def test_last_completed_market_date_should_use_friday_on_saturday() -> None:
    now = datetime(2026, 8, 29, 12, tzinfo=ZoneInfo("America/New_York"))

    assert last_completed_market_date(now).isoformat() == "2026-08-28"


def test_last_completed_market_date_should_use_previous_day_before_settlement() -> None:
    now = datetime(2026, 8, 28, 17, 59, tzinfo=ZoneInfo("America/New_York"))

    assert last_completed_market_date(now).isoformat() == "2026-08-27"


def test_last_completed_market_date_should_use_same_day_after_settlement() -> None:
    now = datetime(2026, 8, 28, 18, 7, tzinfo=ZoneInfo("America/New_York"))

    assert last_completed_market_date(now).isoformat() == "2026-08-28"


def test_write_github_output_should_publish_market_release_paths(tmp_path: Path) -> None:
    path = tmp_path / "github-output"

    write_github_output(path, "mr_test", Path("release.json"), Path("latest.json"))

    assert path.read_text(encoding="utf-8").splitlines() == [
        "market_release_id=mr_test",
        "market_release=release.json",
        "market_latest=latest.json",
    ]
