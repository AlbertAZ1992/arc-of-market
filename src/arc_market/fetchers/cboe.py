"""Cboe VIX current and historical close fetcher."""

from datetime import date
from io import StringIO
from typing import cast

import pandas as pd
import requests

from arc_market.errors import MarketSourceError
from arc_market.models import VixSnapshot

VIX_CSV_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"


def parse_vix_csv(csv_text: str, target_date: date) -> VixSnapshot:
    table = pd.read_csv(StringIO(csv_text))
    table.columns = [str(column).strip().upper() for column in table.columns]
    if not {"DATE", "CLOSE"}.issubset(table.columns):
        raise MarketSourceError("Cboe VIX CSV fields are invalid")
    table["DATE"] = pd.to_datetime(table["DATE"], errors="coerce")
    table["CLOSE"] = pd.to_numeric(table["CLOSE"], errors="coerce")
    table = table.dropna(subset=["DATE", "CLOSE"])
    table = table[table["DATE"].dt.date <= target_date].sort_values("DATE")
    if len(table) < 2 or float(table.iloc[-1]["CLOSE"]) <= 0:
        raise MarketSourceError("Cboe VIX CSV requires two valid closing values")
    row = table.iloc[-1]
    previous = table.iloc[-2]
    as_of = cast(date, pd.Timestamp(row["DATE"]).date())
    previous_as_of = cast(date, pd.Timestamp(previous["DATE"]).date())
    history = table.set_index("DATE")["CLOSE"].copy()
    return VixSnapshot(
        as_of,
        round(float(row["CLOSE"]), 4),
        previous_as_of,
        round(float(previous["CLOSE"]), 4),
        history,
    )


class CboeVixFetcher:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def fetch(self, target_date: date) -> VixSnapshot:
        response = self._session.get(
            VIX_CSV_URL,
            headers={"User-Agent": "ArcOfMarket/2.0"},
            timeout=30,
        )
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            raise MarketSourceError("Cboe VIX request failed") from error
        return parse_vix_csv(response.text, target_date)
