"""CFTC Traders in Financial Futures history for VIX positioning."""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import cast

import pandas as pd
import requests

from arc_market.errors import MarketSourceError
from arc_market.models import CftcSnapshot

CFTC_TFF_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
_DATE_FIELD = "report_date_as_yyyy_mm_dd"
_FIELDS = {
    "leveragedLong": "lev_money_positions_long",
    "leveragedShort": "lev_money_positions_short",
    "assetManagerLong": "asset_mgr_positions_long",
    "assetManagerShort": "asset_mgr_positions_short",
    "openInterest": "open_interest_all",
}


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        raise ValueError("CFTC position field is not numeric")
    return float(value)


def _position_row(row: Mapping[str, object]) -> dict[str, object] | None:
    try:
        report_date = pd.Timestamp(str(row[_DATE_FIELD]))
        values = {name: _number(row[field]) for name, field in _FIELDS.items()}
    except (KeyError, TypeError, ValueError):
        return None
    open_interest = values["openInterest"]
    if open_interest <= 0:
        return None
    leveraged = values["leveragedLong"] - values["leveragedShort"]
    asset_manager = values["assetManagerLong"] - values["assetManagerShort"]
    return {
        "date": report_date,
        "leveragedNetPctOi": leveraged / open_interest * 100,
        "assetManagerNetPctOi": asset_manager / open_interest * 100,
    }


def parse_cftc_rows(
    rows: Sequence[Mapping[str, object]],
    target_date: date,
    *,
    minimum_rows: int = 100,
) -> CftcSnapshot:
    normalized = [value for row in rows if (value := _position_row(row)) is not None]
    table = pd.DataFrame(normalized)
    if table.empty:
        raise MarketSourceError("CFTC TFF returned no valid VIX positioning rows")
    table = table[pd.to_datetime(table["date"]).dt.date <= target_date]
    table = table.drop_duplicates("date", keep="last").sort_values("date")
    if len(table) < minimum_rows:
        raise MarketSourceError(f"CFTC VIX positioning coverage is too low: {len(table)} rows")
    history = table.set_index("date").loc[:, ["leveragedNetPctOi", "assetManagerNetPctOi"]]
    history = history.round(4)
    as_of = cast(date, pd.Timestamp(history.index[-1]).date())
    return CftcSnapshot(as_of, history)


class CftcFetcher:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def fetch(self, target_date: date) -> CftcSnapshot:
        selected = ",".join((_DATE_FIELD, *_FIELDS.values()))
        try:
            response = self._session.get(
                CFTC_TFF_URL,
                params={
                    "$limit": "5000",
                    "$order": f"{_DATE_FIELD} ASC",
                    "$select": selected,
                    "$where": "starts_with(market_and_exchange_names,'VIX')",
                },
                headers={"User-Agent": "ArcOfMarket/2.0"},
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise MarketSourceError("CFTC TFF request failed") from error
        if not isinstance(payload, list):
            raise MarketSourceError("CFTC TFF response is not an array")
        rows = [row for row in payload if isinstance(row, dict)]
        return parse_cftc_rows(rows, target_date)
