"""Export temporary adjusted QQQ/VTV bars for the canonical strategy replay."""

import argparse
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

SYMBOLS = ("QQQ", "VTV")


def adjusted_bars(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Normalize yfinance adjusted open/close output into the cloud replay contract."""
    columns = {
        (field, symbol): _series(frame, field, symbol)
        for field in ("Open", "Close")
        for symbol in SYMBOLS
    }
    normalized = pd.DataFrame(columns).dropna().sort_index()
    if normalized.empty:
        raise ValueError("Yahoo returned no complete QQQ/VTV sessions")
    if (normalized <= 0).any(axis=None):
        raise ValueError("Adjusted backtest prices must be positive")
    if normalized.index.duplicated().any() or not normalized.index.is_monotonic_increasing:
        raise ValueError("Adjusted backtest sessions must be unique and ordered")
    return [
        {
            "asOf": pd.Timestamp(str(index)).date().isoformat(),
            "qqqOpen": float(row[("Open", "QQQ")]),
            "qqqClose": float(row[("Close", "QQQ")]),
            "vtvOpen": float(row[("Open", "VTV")]),
            "vtvClose": float(row[("Close", "VTV")]),
        }
        for index, row in normalized.iterrows()
    ]


def _series(frame: pd.DataFrame, field: str, symbol: str) -> pd.Series:
    if not isinstance(frame.columns, pd.MultiIndex):
        raise ValueError("Yahoo backtest response must contain field and ticker levels")
    first = frame.columns.get_level_values(0)
    second = frame.columns.get_level_values(1)
    if field in first and symbol in second:
        return frame[(field, symbol)].rename((field, symbol))
    if symbol in first and field in second:
        return frame[(symbol, field)].rename((field, symbol))
    raise ValueError(f"Yahoo backtest response is missing {symbol} {field}")


def download(start: date, end: date) -> pd.DataFrame:
    return yf.download(
        list(SYMBOLS),
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        interval="1d",
        auto_adjust=True,
        actions=False,
        repair=False,
        progress=False,
        threads=True,
        group_by="column",
        multi_level_index=True,
        timeout=30,
    )


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=date.fromisoformat, default=date(2004, 1, 30))
    parser.add_argument("--end", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path, default=Path("outputs/core-rotation-bars.json"))
    return parser.parse_args()


def main() -> None:
    options = arguments()
    if options.start >= options.end:
        raise ValueError("Backtest start must be before end")
    bars = adjusted_bars(download(options.start, options.end))
    payload = {
        "schemaVersion": "1.0",
        "priceBasis": "Yahoo Finance auto-adjusted open and close",
        "generatedAt": datetime.now(UTC).isoformat(),
        "bars": bars,
    }
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
    print(f"Wrote {len(bars)} sessions through {bars[-1]['asOf']} to {options.output}")


if __name__ == "__main__":
    main()
