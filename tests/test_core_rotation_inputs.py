import pandas as pd
import pytest

from arc_market.strategy_inputs import core_rotation_inputs


def prices(periods: int = 300) -> pd.DataFrame:
    return pd.DataFrame(
        {"QQQ": [100.0 + step for step in range(periods)], "VTV": 100.0},
        index=pd.bdate_range(end="2026-09-03", periods=periods),
    )


def test_core_rotation_inputs_preserves_roc35_and_provides_guard_evidence() -> None:
    frame = prices()
    result = core_rotation_inputs(frame)

    assert result is not None
    assert result["asOf"] == "2026-09-03"
    assert result["previousSession"] == "2026-09-02"
    assert result["ma50"] == 374.5
    assert result["ma200"] == 299.5
    assert result["ma50FiveSessionsAgo"] == 369.5
    assert result["roc35"] == pytest.approx((364 / 399 - 1) * 100)
    assert result["recentHigh"] is True
    assert "target" not in result
    assert "vix" not in result


def test_core_rotation_inputs_does_not_fill_short_or_missing_history() -> None:
    assert core_rotation_inputs(prices(270)) is None
    missing = prices()
    missing.iloc[-10, 0] = float("nan")
    assert core_rotation_inputs(missing) is None
    invalid = prices()
    invalid.iloc[-10, 0] = 0
    assert core_rotation_inputs(invalid) is None


def test_high_zone_is_evaluated_at_each_historical_date_not_against_todays_high() -> None:
    frame = prices(300)
    frame["QQQ"] = 100.0
    frame.iloc[-19:, 0] = 90.0
    assert core_rotation_inputs(frame)["recentHigh"] is True
    frame.iloc[-20:, 0] = 90.0
    assert core_rotation_inputs(frame)["recentHigh"] is False
