import pandas as pd
import pytest
from scripts.index_statistics import (
    annual_return_distribution,
    extreme_day_summary,
    holding_period_summary,
    market_cycles,
    rolling_cagr_payload,
    volatility_history,
)


def test_annual_return_distribution_excludes_current_year() -> None:
    close = pd.Series(
        [100.0, 80.0, 88.0, 123.2],
        index=pd.to_datetime(["2022-12-30", "2023-12-29", "2024-12-31", "2025-12-31"]),
    )

    result = annual_return_distribution(close, current_year=2025)

    assert result["years_total"] == 2
    assert result["buckets"][2] == {
        "label": "-20~-10%",
        "count": 1,
        "years": [2023],
    }
    assert result["buckets"][5] == {
        "label": "10~20%",
        "count": 1,
        "years": [2024],
    }


def test_holding_summary_and_rolling_cagr_use_month_end_observations() -> None:
    index = pd.date_range("2000-01-31", periods=300, freq="ME")
    month_end = pd.Series([100 * (1.01**month) for month in range(300)], index=index)

    holding = holding_period_summary(month_end)
    rolling = rolling_cagr_payload(month_end)

    assert [row["years"] for row in holding["rows"]] == [1, 3, 5, 10, 20]
    assert holding["rows"][0]["win"] == 100.0
    assert rolling["cagr5"][-1] == pytest.approx(12.68, abs=0.01)
    assert rolling["cagr20"][-1] == pytest.approx(12.68, abs=0.01)


def test_market_cycles_confirm_threshold_turning_points() -> None:
    close = pd.Series(
        [100.0, 120.0, 95.0, 90.0, 115.0, 110.0],
        index=pd.date_range("2025-01-01", periods=6, freq="D"),
    )

    result = market_cycles(close)

    assert result["cycles"] == [
        {
            "kind": "bull",
            "start": "2025-01-01",
            "end": "2025-01-02",
            "ret": 20.0,
            "days": 1,
        },
        {
            "kind": "bear",
            "start": "2025-01-02",
            "end": "2025-01-04",
            "ret": -25.0,
            "days": 2,
        },
        {
            "kind": "bull",
            "start": "2025-01-04",
            "end": None,
            "ret": 22.2,
            "days": 2,
        },
    ]


def test_extreme_day_summary_counts_all_returns_once() -> None:
    close = pd.Series(
        [100.0, 94.0, 95.0, 100.0],
        index=pd.date_range("2025-01-01", periods=4, freq="D"),
    )

    result = extreme_day_summary(close)

    assert result["days_total"] == 3
    assert sum(bucket["count"] for bucket in result["hist"]) == 3
    assert result["worst"][0] == {"date": "2025-01-02", "ret": -6.0}


def test_volatility_history_omits_incomplete_rolling_windows() -> None:
    close = pd.Series(
        range(100, 180),
        index=pd.date_range("2025-01-01", periods=80, freq="D"),
        dtype=float,
    )

    result = volatility_history(close)

    assert result["dates"]
    assert len(result["dates"]) == len(result["vol20"]) == len(result["vol60"])
    assert all(pd.notna(value) for value in result["vol60"])
