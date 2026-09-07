"""Official U.S. Treasury daily par-yield curve fetcher."""

from datetime import date
from io import StringIO
from typing import cast

import pandas as pd
import requests

from arc_market.errors import MarketSourceError
from arc_market.models import TreasurySnapshot

TREASURY_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "TextView?type=daily_treasury_yield_curve&field_tdr_date_value={year}"
)


def _basis_point_change(values: pd.Series, sessions: int) -> float:
    return round(float(values.iloc[-1] - values.iloc[-sessions - 1]) * 100, 2)


def parse_treasury_table(table: pd.DataFrame, target_date: date) -> TreasurySnapshot:
    required = {"Date", "2 Yr", "10 Yr"}
    if not required.issubset(table.columns):
        raise MarketSourceError("Treasury yield table fields are invalid")
    selected = table.loc[:, ["Date", "2 Yr", "10 Yr"]].copy()
    selected["Date"] = pd.to_datetime(selected["Date"], errors="coerce")
    for field in ("2 Yr", "10 Yr"):
        selected[field] = pd.to_numeric(selected[field], errors="coerce")
    selected = selected.dropna().drop_duplicates("Date", keep="last").sort_values("Date")
    selected = selected[selected["Date"].dt.date <= target_date]
    if len(selected) < 4:
        raise MarketSourceError("Treasury yield table requires four observations")
    row = selected.iloc[-1]
    as_of = cast(date, pd.Timestamp(row["Date"]).date())
    return TreasurySnapshot(
        as_of=as_of,
        treasury_2y=round(float(row["2 Yr"]), 4),
        treasury_10y=round(float(row["10 Yr"]), 4),
        treasury_2y_change_1d_bp=_basis_point_change(selected["2 Yr"], 1),
        treasury_10y_change_1d_bp=_basis_point_change(selected["10 Yr"], 1),
        treasury_10y_change_3d_bp=_basis_point_change(selected["10 Yr"], 3),
    )


class TreasuryFetcher:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def fetch(self, target_date: date) -> TreasurySnapshot:
        try:
            response = self._session.get(
                TREASURY_URL.format(year=target_date.year),
                headers={"User-Agent": "ArcOfMarket/2.0"},
                timeout=30,
            )
            response.raise_for_status()
            tables = pd.read_html(StringIO(response.text))
        except (requests.RequestException, ValueError) as error:
            raise MarketSourceError("U.S. Treasury yield request failed") from error
        if not tables:
            raise MarketSourceError("U.S. Treasury response contains no yield table")
        return parse_treasury_table(tables[0], target_date)
