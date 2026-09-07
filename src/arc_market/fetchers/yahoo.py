"""Yahoo Finance adjusted-close fetching without persistent raw output."""

import logging
from collections.abc import Callable, Sequence
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from arc_market.errors import MarketSourceError

Downloader = Callable[..., pd.DataFrame]


def _close_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame.columns, pd.MultiIndex):
        if "Close" not in frame:
            raise MarketSourceError("Yahoo response has no Close column")
        close = frame[["Close"]].copy()
        return close
    first = frame.columns.get_level_values(0)
    second = frame.columns.get_level_values(1)
    if "Close" in first:
        return frame.xs("Close", axis=1, level=0, drop_level=True).copy()
    if "Close" in second:
        return frame.xs("Close", axis=1, level=1, drop_level=True).copy()
    raise MarketSourceError("Yahoo response has no Close price level")


def normalize_close_frame(
    frame: pd.DataFrame,
    symbols: Sequence[str],
    target_date: date,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        raise MarketSourceError("Yahoo response is empty")
    close = _close_columns(frame)
    if len(symbols) == 1 and list(close.columns) == ["Close"]:
        close.columns = [symbols[0]]
    close.columns = [str(column).upper() for column in close.columns]
    normalized_index = pd.DatetimeIndex(
        [pd.Timestamp(item).tz_localize(None).date() for item in close.index]
    )
    close.index = normalized_index
    close = close.loc[close.index <= pd.Timestamp(target_date)]
    close = close[~close.index.duplicated(keep="last")].sort_index()
    available = [symbol for symbol in symbols if symbol in close]
    if not available:
        raise MarketSourceError("Yahoo response contains none of the requested symbols")
    close = close.loc[:, available].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    if close.empty:
        raise MarketSourceError("Yahoo response contains no numeric close values")
    return close


class YahooPriceFetcher:
    def __init__(self, *, downloader: Downloader = yf.download, chunk_size: int = 100) -> None:
        self._downloader = downloader
        self._chunk_size = chunk_size

    def _download(self, symbols: tuple[str, ...], target_date: date) -> pd.DataFrame:
        start = target_date - timedelta(days=550)
        end = target_date + timedelta(days=1)
        logger = logging.getLogger("yfinance")
        previous_level = logger.level
        try:
            logger.setLevel(logging.CRITICAL)
            frame = self._downloader(
                list(symbols),
                start=start.isoformat(),
                end=end.isoformat(),
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
        finally:
            logger.setLevel(previous_level)
        try:
            return normalize_close_frame(frame, symbols, target_date)
        except MarketSourceError as error:
            names = ", ".join(symbols)
            raise MarketSourceError(f"Yahoo batch failed for {names}: {error}") from error

    def fetch(self, symbols: Sequence[str], target_date: date) -> pd.DataFrame:
        unique = tuple(dict.fromkeys(symbol.upper() for symbol in symbols))
        if not unique:
            raise MarketSourceError("Yahoo symbol list is empty")
        frames = []
        for offset in range(0, len(unique), self._chunk_size):
            frames.append(self._download(unique[offset : offset + self._chunk_size], target_date))
        combined = pd.concat(frames, axis=1)
        combined = combined.loc[:, ~combined.columns.duplicated(keep="last")]
        missing = tuple(
            symbol for symbol in unique if symbol not in combined or combined[symbol].dropna().empty
        )
        if missing:
            retry = self._download(missing, target_date)
            combined = pd.concat([combined, retry], axis=1)
            combined = combined.loc[:, ~combined.columns.duplicated(keep="last")]
        return combined.sort_index()
