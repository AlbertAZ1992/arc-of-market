from datetime import date

import pandas as pd

from arc_market.fetchers.cboe import parse_vix_csv
from arc_market.fetchers.fred import parse_fred_csv
from arc_market.fetchers.ofr import parse_ofr_csv
from arc_market.fetchers.treasury import parse_treasury_table
from arc_market.fetchers.wikipedia import parse_universe_tables
from arc_market.fetchers.yahoo import (
    YahooPriceFetcher,
    latest_intraday_closes,
    normalize_close_frame,
)


def test_normalize_close_frame_should_handle_yfinance_multi_index() -> None:
    index = pd.to_datetime(["2026-08-27", "2026-08-28"])
    columns = pd.MultiIndex.from_tuples(
        [("Close", "SPY"), ("Close", "QQQ"), ("Volume", "SPY")],
        names=["Price", "Ticker"],
    )
    frame = pd.DataFrame([[100.0, 200.0, 10], [101.0, 202.0, 20]], index=index, columns=columns)

    result = normalize_close_frame(frame, ("SPY", "QQQ"), date(2026, 8, 28))

    assert list(result.columns) == ["SPY", "QQQ"]
    assert result.index[-1].date() == date(2026, 8, 28)
    assert float(result.loc["2026-08-28", "QQQ"]) == 202.0


def test_yahoo_fetcher_should_fill_missing_daily_close_from_intraday() -> None:
    intervals: list[str] = []

    def download(_symbols: list[str], **kwargs: object) -> pd.DataFrame:
        intervals.append(str(kwargs["interval"]))
        if kwargs["interval"] == "1h":
            return pd.DataFrame(
                {"Close": [101.5, 102.0]},
                index=pd.to_datetime(["2026-08-28 14:30", "2026-08-28 15:30"]),
            )
        return pd.DataFrame(
            {"Close": [100.0, float("nan")]},
            index=pd.to_datetime(["2026-08-27", "2026-08-28"]),
        )

    result = YahooPriceFetcher(downloader=download).fetch(("SPY",), date(2026, 8, 28))

    assert intervals == ["1d", "1h"]
    assert result.index[-1].date() == date(2026, 8, 28)
    assert float(result.loc["2026-08-28", "SPY"]) == 102.0


def test_latest_intraday_closes_should_use_last_non_null_price_per_symbol() -> None:
    columns = pd.MultiIndex.from_tuples(
        [("Close", "SPY"), ("Close", "QQQ")],
        names=["Price", "Ticker"],
    )
    frame = pd.DataFrame(
        [[100.0, 200.0], [101.0, float("nan")], [float("nan"), 202.0]],
        index=pd.to_datetime(["2026-08-28 14:30", "2026-08-28 15:00", "2026-08-28 15:30"]),
        columns=columns,
    )

    result = latest_intraday_closes(frame, ("SPY", "QQQ"), date(2026, 8, 28))

    assert result == {"SPY": 101.0, "QQQ": 202.0}


def test_yahoo_fetcher_should_retry_missing_batch_symbols() -> None:
    calls: list[tuple[str, ...]] = []

    def download(symbols: list[str], **_kwargs: object) -> pd.DataFrame:
        requested = tuple(symbols)
        calls.append(requested)
        returned = ("SPY",) if requested == ("SPY", "QQQ") else requested
        columns = pd.MultiIndex.from_tuples(
            [("Close", symbol) for symbol in returned],
            names=["Price", "Ticker"],
        )
        return pd.DataFrame(
            [[100.0 for _symbol in returned], [101.0 for _symbol in returned]],
            index=pd.to_datetime(["2026-08-27", "2026-08-28"]),
            columns=columns,
        )

    result = YahooPriceFetcher(downloader=download).fetch(("SPY", "QQQ"), date(2026, 8, 28))

    assert calls == [("SPY", "QQQ"), ("QQQ",), ("QQQ",)]
    assert list(result) == ["SPY", "QQQ"]


def test_yahoo_fetcher_should_retry_stale_batch_symbol_individually() -> None:
    intraday_calls: list[tuple[str, ...]] = []

    def download(symbols: list[str], **kwargs: object) -> pd.DataFrame:
        requested = tuple(symbols)
        if kwargs["interval"] == "1d":
            columns = pd.MultiIndex.from_tuples(
                [("Close", symbol) for symbol in requested],
                names=["Price", "Ticker"],
            )
            return pd.DataFrame(
                [[100.0 for _symbol in requested]],
                index=pd.to_datetime(["2026-08-27"]),
                columns=columns,
            )
        intraday_calls.append(requested)
        returned = ("SPY",) if requested == ("SPY", "QQQ") else requested
        columns = pd.MultiIndex.from_tuples(
            [("Close", symbol) for symbol in returned],
            names=["Price", "Ticker"],
        )
        return pd.DataFrame(
            [[101.0 for _symbol in returned]],
            index=pd.to_datetime(["2026-08-28 15:30"]),
            columns=columns,
        )

    result = YahooPriceFetcher(downloader=download).fetch(("SPY", "QQQ"), date(2026, 8, 28))

    assert intraday_calls == [("SPY", "QQQ"), ("QQQ",)]
    assert result.loc["2026-08-28"].to_dict() == {"SPY": 101.0, "QQQ": 101.0}


def test_parse_fred_csv_should_return_named_numeric_series() -> None:
    csv = "observation_date,SOFR,DGS10\n2026-08-27,5.25,.\n2026-08-28,5.24,4.20\n"

    result = parse_fred_csv(csv.encode(), ("SOFR", "DGS10"), date(2026, 8, 28))

    assert float(result["SOFR"].iloc[-1]) == 5.24
    assert result["DGS10"].index[-1].date() == date(2026, 8, 28)


def test_parse_vix_csv_should_keep_only_latest_value() -> None:
    csv = "DATE,OPEN,HIGH,LOW,CLOSE\n08/27/2026,16,18,15,17.2\n08/28/2026,17,19,16,18.4\n"

    result = parse_vix_csv(csv, date(2026, 8, 29))

    assert result.as_of == date(2026, 8, 28)
    assert result.value == 18.4
    assert result.previous_as_of == date(2026, 8, 27)
    assert result.previous_value == 17.2


def test_parse_treasury_table_should_calculate_daily_and_three_day_changes() -> None:
    table = pd.DataFrame(
        {
            "Date": ["08/24/2026", "08/25/2026", "08/26/2026", "08/27/2026"],
            "2 Yr": [4.10, 4.12, 4.15, 4.20],
            "10 Yr": [4.60, 4.62, 4.66, 4.67],
        }
    )

    result = parse_treasury_table(table, date(2026, 8, 27))

    assert result.as_of == date(2026, 8, 27)
    assert result.treasury_2y == 4.2
    assert result.treasury_10y == 4.67
    assert result.treasury_10y_change_1d_bp == 1.0
    assert result.treasury_10y_change_3d_bp == 7.0


def test_parse_ofr_csv_should_keep_latest_compact_components() -> None:
    csv = (
        "Date,OFR FSI,Credit,Equity valuation,Safe assets,Funding,Volatility,"
        "United States,Other advanced economies,Emerging markets\n"
        "2026-08-28,0.5,0.1,0.2,0.0,0.1,0.1,0.3,0.1,0.1\n"
    )

    result = parse_ofr_csv(csv, date(2026, 8, 29), minimum_rows=1)

    assert result.as_of == date(2026, 8, 28)
    assert result.value == 0.5
    assert result.components["credit"] == 0.1
    assert result.regions["unitedStates"] == 0.3


def test_parse_universe_tables_should_normalize_yahoo_tickers() -> None:
    tables = {
        "sp500": [pd.DataFrame({"Symbol": ["BRK.B", "AAPL"]})],
        "nasdaq100": [pd.DataFrame({"Ticker": ["GOOGL", "GOOG"]})],
        "dow30": [pd.DataFrame({"Symbol": [f"D{index}" for index in range(30)]})],
    }

    result = parse_universe_tables(tables, observed_at=date(2026, 8, 29))

    assert result["sp500"].members == ("BRK-B", "AAPL")
    assert result["nasdaq100"].members == ("GOOGL", "GOOG")
    assert len(result["dow30"].members) == 30
