"""Office of Financial Research FSI current snapshot and history fetcher."""

from datetime import date
from io import StringIO
from typing import cast

import pandas as pd
import requests

from arc_market.errors import MarketSourceError
from arc_market.models import OfrSnapshot

OFR_CSV_URL = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"
_COMPONENTS = {
    "credit": "Credit",
    "equityValuation": "Equity valuation",
    "safeAssets": "Safe assets",
    "funding": "Funding",
    "volatility": "Volatility",
}
_REGIONS = {
    "unitedStates": "United States",
    "otherAdvancedEconomies": "Other advanced economies",
    "emergingMarkets": "Emerging markets",
}


def parse_ofr_csv(csv_text: str, target_date: date, *, minimum_rows: int = 5_000) -> OfrSnapshot:
    table = pd.read_csv(StringIO(csv_text))
    required = ["Date", "OFR FSI", *_COMPONENTS.values(), *_REGIONS.values()]
    missing = [column for column in required if column not in table]
    if missing:
        raise MarketSourceError(f"OFR CSV is missing columns: {', '.join(missing)}")
    table["Date"] = pd.to_datetime(table["Date"], errors="coerce")
    for column in required[1:]:
        table[column] = pd.to_numeric(table[column], errors="coerce")
    table = table.dropna(subset=required)
    table = table[table["Date"].dt.date <= target_date].sort_values("Date")
    if len(table) < minimum_rows:
        raise MarketSourceError(f"OFR FSI coverage is too low: {len(table)} rows")
    row = table.iloc[-1]
    as_of = cast(date, pd.Timestamp(row["Date"]).date())
    renamed = {
        "OFR FSI": "fsi",
        **{column: key for key, column in _COMPONENTS.items()},
        **{column: key for key, column in _REGIONS.items()},
    }
    history = table.set_index("Date").rename(columns=renamed).loc[:, list(renamed.values())]
    return OfrSnapshot(
        as_of,
        round(float(row["OFR FSI"]), 4),
        {key: round(float(row[column]), 4) for key, column in _COMPONENTS.items()},
        {key: round(float(row[column]), 4) for key, column in _REGIONS.items()},
        history,
    )


class OfrFetcher:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def fetch(self, target_date: date) -> OfrSnapshot:
        response = self._session.get(
            OFR_CSV_URL,
            headers={"User-Agent": "ArcOfMarket/2.0"},
            timeout=60,
        )
        try:
            response.raise_for_status()
        except requests.RequestException as error:
            raise MarketSourceError("OFR request failed") from error
        return parse_ofr_csv(response.text, target_date)
