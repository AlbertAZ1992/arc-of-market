"""Fetch current U.S. equity profiles used by the market treemap."""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

import requests

from arc_market.errors import MarketSourceError
from arc_market.models import MarketProfile, MarketProfileSnapshot

_URL = "https://api.nasdaq.com/api/screener/stocks"
_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (compatible; ArcOfMarket/2.0)",
}


def _ticker(value: object) -> str:
    return str(value).strip().upper().replace(".", "-")


def _market_cap(value: object) -> float | None:
    try:
        parsed = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def parse_stock_screener(
    document: Mapping[str, Any],
    symbols: Sequence[str],
) -> dict[str, MarketProfile]:
    data = document.get("data")
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise MarketSourceError("Nasdaq stock screener response has no rows")
    requested = set(symbols)
    profiles: dict[str, MarketProfile] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = _ticker(row.get("symbol"))
        market_cap = _market_cap(row.get("marketCap"))
        name = row.get("name")
        sector = row.get("sector")
        if (
            ticker not in requested
            or market_cap is None
            or not isinstance(name, str)
            or not isinstance(sector, str)
            or not name.strip()
            or not sector.strip()
        ):
            continue
        profiles[ticker] = MarketProfile(name.strip(), sector.strip(), market_cap)
    if not profiles:
        raise MarketSourceError("Nasdaq stock screener matched no requested symbols")
    return profiles


class NasdaqMarketProfileFetcher:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def fetch(self, symbols: Sequence[str], target_date: date) -> MarketProfileSnapshot:
        try:
            response = self._session.get(
                _URL,
                params={"tableonly": "true", "limit": 10_000, "offset": 0, "download": "true"},
                headers=_HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            document = response.json()
        except (requests.RequestException, ValueError) as error:
            raise MarketSourceError("Nasdaq stock screener request failed") from error
        if not isinstance(document, dict):
            raise MarketSourceError("Nasdaq stock screener response is invalid")
        return MarketProfileSnapshot(target_date, parse_stock_screener(document, symbols))
