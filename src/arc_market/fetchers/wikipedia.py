"""Current-universe ticker fetcher for breadth calculation."""

from collections.abc import Mapping, Sequence
from datetime import date
from io import StringIO

import pandas as pd
import requests

from arc_market.errors import MarketSourceError
from arc_market.models import UniverseSnapshot

_URLS = {
    "sp500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    "nasdaq100": "https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies",
    "dow30": "https://en.wikipedia.org/wiki/List_of_Dow_Jones_Industrial_Average_companies",
}
_COLUMNS = {"sp500": "Symbol", "nasdaq100": "Ticker", "dow30": "Symbol"}
_MINIMUM_COUNTS = {"sp500": 490, "nasdaq100": 95, "dow30": 30}
_USER_AGENT = "ArcOfMarket/2.0 (+https://github.com/AlbertAZ1992/arc-of-market)"


def _normalize_ticker(value: object) -> str:
    return str(value).strip().upper().replace(".", "-")


def _constituent_table(index_id: str, tables: Sequence[pd.DataFrame]) -> pd.DataFrame:
    column = _COLUMNS[index_id]
    table = next((candidate for candidate in tables if column in candidate.columns), None)
    if table is None:
        raise MarketSourceError(f"Wikipedia {index_id} constituent table was not found")
    return table


def _members(index_id: str, table: pd.DataFrame) -> tuple[str, ...]:
    column = _COLUMNS[index_id]
    values = tuple(dict.fromkeys(_normalize_ticker(value) for value in table[column].dropna()))
    if not values:
        raise MarketSourceError(f"Wikipedia {index_id} constituent table is empty")
    return values


def _sp500_metadata(table: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    required = {"Symbol", "Security", "GICS Sector"}
    if not required.issubset(table.columns):
        return {}, {}
    names: dict[str, str] = {}
    sectors: dict[str, str] = {}
    for _, row in table.iterrows():
        ticker = _normalize_ticker(row["Symbol"])
        names[ticker] = str(row["Security"]).strip()
        sectors[ticker] = str(row["GICS Sector"]).strip()
    return names, sectors


def parse_universe_tables(
    tables: Mapping[str, Sequence[pd.DataFrame]],
    *,
    observed_at: date,
) -> dict[str, UniverseSnapshot]:
    snapshots: dict[str, UniverseSnapshot] = {}
    for index_id in ("sp500", "nasdaq100", "dow30"):
        table = _constituent_table(index_id, tables[index_id])
        names, sectors = _sp500_metadata(table) if index_id == "sp500" else ({}, {})
        snapshots[index_id] = UniverseSnapshot(
            _members(index_id, table),
            observed_at,
            "wikipedia",
            names,
            sectors,
        )
    return snapshots


class WikipediaUniverseFetcher:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def _tables(self, index_id: str) -> list[pd.DataFrame]:
        try:
            response = self._session.get(
                _URLS[index_id],
                headers={"User-Agent": _USER_AGENT, "Api-User-Agent": _USER_AGENT},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise MarketSourceError(f"Wikipedia {index_id} request failed") from error
        return pd.read_html(StringIO(response.text))

    def fetch(self, observed_at: date) -> dict[str, UniverseSnapshot]:
        result = parse_universe_tables(
            {index_id: self._tables(index_id) for index_id in _URLS},
            observed_at=observed_at,
        )
        for index_id, snapshot in result.items():
            if len(snapshot.members) < _MINIMUM_COUNTS[index_id]:
                count = len(snapshot.members)
                raise MarketSourceError(f"Wikipedia {index_id} member count is too low: {count}")
        return result
