from datetime import UTC, date, datetime

import pandas as pd
import pytest

from arc_market.rotation_history import build_rotation_history


def prices() -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=320)
    return pd.DataFrame(
        {"QQQ": [500 + i for i in range(320)], "VTV": [200 + i / 5 for i in range(320)]},
        index=dates,
    )


def history(frame: pd.DataFrame) -> dict[str, object]:
    return build_rotation_history(
        frame,
        start=frame.index[-24].date(),
        end=frame.index[-1].date(),
        computed_at=datetime(2026, 9, 4, tzinfo=UTC),
    )


def test_backfill_uses_only_prices_available_at_each_session() -> None:
    frame = prices()
    result = history(frame)
    entries = result["entries"]
    assert isinstance(entries, list)
    assert len(entries) == 24
    first = entries[0]
    as_of = pd.Timestamp(first["asOf"])
    point_in_time = frame.loc[:as_of]
    ratio = point_in_time["VTV"] / point_in_time["QQQ"]
    expected = (ratio.iloc[-1] / ratio.iloc[-36] - 1) * 100
    assert float(first["value"]) == round(expected, 4)
    assert first["qqq"]["ma50"] == round(point_in_time["QQQ"].tail(50).mean(), 4)
    assert first["strategyInputs"]["asOf"] == first["asOf"]
    assert first["strategyInputs"]["previousSession"] == point_in_time.index[-2].date().isoformat()
    assert first["strategyInputs"]["ma200"] == point_in_time["QQQ"].tail(200).mean()
    assert len(first["strategyInputs"]["calculationDigest"]) == 64
    assert first["reconstruction"]["computedAt"].startswith("2026-09-04")
    changed = frame.copy()
    changed.loc[changed.index > as_of, "QQQ"] *= 2
    changed_result = history(changed)["entries"]
    assert isinstance(changed_result, list)
    assert changed_result[0] == first


def test_backfill_is_deterministic_and_uses_real_sessions_only() -> None:
    result = history(prices())
    assert result == history(prices())
    entries = result["entries"]
    assert isinstance(entries, list)
    assert all(date.fromisoformat(row["asOf"]).weekday() < 5 for row in entries)
    assert all(row["event"] == "UNCHANGED" for row in entries)
    assert all(row["state"] == "GROWTH_LEADING" for row in entries)


@pytest.mark.parametrize("invalid", ["duplicate", "missing", "nonfinite", "nonpositive"])
def test_backfill_rejects_incomplete_or_invalid_prices(invalid: str) -> None:
    frame = prices()
    if invalid == "duplicate":
        frame = pd.concat([frame, frame.tail(1)])
    elif invalid == "missing":
        frame.loc[frame.index[-5], "VTV"] = float("nan")
    elif invalid == "nonfinite":
        frame.loc[frame.index[-5], "VTV"] = float("inf")
    else:
        frame.loc[frame.index[-5], "VTV"] = 0
    with pytest.raises(ValueError):
        history(frame)


def test_backfill_requires_warmup_and_a_nonempty_date_range() -> None:
    with pytest.raises(ValueError):
        history(prices().tail(30))
    with pytest.raises(ValueError):
        build_rotation_history(
            prices(),
            start=date(2026, 8, 1),
            end=date(2026, 7, 1),
            computed_at=datetime(2026, 9, 4, tzinfo=UTC),
        )
