import pandas as pd
import pytest
from scripts.export_rotation_backtest_bars import adjusted_bars


def yahoo_frame() -> pd.DataFrame:
    columns = pd.MultiIndex.from_tuples(
        [
            ("Open", "QQQ"),
            ("Open", "VTV"),
            ("Close", "QQQ"),
            ("Close", "VTV"),
        ]
    )
    return pd.DataFrame(
        [[100.0, 80.0, 101.0, 81.0], [102.0, 82.0, 103.0, 83.0]],
        columns=columns,
        index=pd.to_datetime(["2026-09-09", "2026-09-10"]),
    )


def test_adjusted_bars_normalizes_complete_sessions() -> None:
    assert adjusted_bars(yahoo_frame()) == [
        {
            "asOf": "2026-09-09",
            "qqqOpen": 100.0,
            "qqqClose": 101.0,
            "vtvOpen": 80.0,
            "vtvClose": 81.0,
        },
        {
            "asOf": "2026-09-10",
            "qqqOpen": 102.0,
            "qqqClose": 103.0,
            "vtvOpen": 82.0,
            "vtvClose": 83.0,
        },
    ]


def test_adjusted_bars_rejects_nonpositive_prices() -> None:
    frame = yahoo_frame()
    frame.loc[pd.Timestamp("2026-09-10"), ("Open", "QQQ")] = 0

    with pytest.raises(ValueError, match="positive"):
        adjusted_bars(frame)
