"""FRED public graph CSV fetcher for reviewed government series."""

from collections.abc import Sequence
from datetime import date
from io import BytesIO, StringIO
from urllib.parse import urlencode
from zipfile import ZipFile, is_zipfile

import pandas as pd
import requests

from arc_market.errors import MarketSourceError

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_USER_AGENT = "ArcOfMarket/2.0 (+https://github.com/AlbertAZ1992/arc-of-market)"


def _fred_table(content: bytes) -> pd.DataFrame:
    if is_zipfile(BytesIO(content)):
        with ZipFile(BytesIO(content)) as archive:
            names = [name for name in archive.namelist() if name.endswith(".csv")]
            if not names:
                raise MarketSourceError("FRED ZIP contains no CSV files")
            frames = [
                pd.read_csv(archive.open(name)).set_index("observation_date") for name in names
            ]
        return pd.concat(frames, axis="columns").reset_index()
    return pd.read_csv(StringIO(content.decode("utf-8")))


def parse_fred_csv(
    content: bytes,
    series_ids: Sequence[str],
    target_date: date,
) -> dict[str, pd.Series]:
    table = _fred_table(content)
    if "observation_date" not in table:
        raise MarketSourceError("FRED CSV has no observation_date column")
    missing = [series_id for series_id in series_ids if series_id not in table]
    if missing:
        raise MarketSourceError(f"FRED CSV is missing series: {', '.join(missing)}")
    table["observation_date"] = pd.to_datetime(table["observation_date"], errors="coerce")
    table = table.dropna(subset=["observation_date"])
    table = table[table["observation_date"].dt.date <= target_date]
    table = table.drop_duplicates("observation_date", keep="last").set_index("observation_date")
    result = {}
    for series_id in series_ids:
        values = pd.to_numeric(table[series_id], errors="coerce").dropna().sort_index()
        if values.empty:
            raise MarketSourceError(f"FRED {series_id} has no numeric observations")
        result[series_id] = values
    return result


class FredFetcher:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()
        self._direct_first = session is None

    def _get(self, url: str) -> bytes:
        if not self._direct_first:
            try:
                response = self._session.get(url, headers={"User-Agent": _USER_AGENT}, timeout=60)
                response.raise_for_status()
                return response.content
            except requests.RequestException as error:
                raise MarketSourceError("FRED request failed") from error
        direct = requests.Session()
        direct.trust_env = False
        try:
            response = direct.get(url, headers={"User-Agent": _USER_AGENT}, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.RequestException:
            try:
                response = self._session.get(url, headers={"User-Agent": _USER_AGENT}, timeout=60)
                response.raise_for_status()
                return response.content
            except requests.RequestException as error:
                raise MarketSourceError(
                    "FRED request failed through proxy and direct routes"
                ) from error
        finally:
            direct.close()

    def fetch(self, series_ids: Sequence[str], target_date: date) -> dict[str, pd.Series]:
        unique = tuple(dict.fromkeys(series_ids))
        result = {}
        for offset in range(0, len(unique), 10):
            batch = unique[offset : offset + 10]
            query = urlencode({"cosd": "1945-01-01", "id": ",".join(batch)})
            content = self._get(f"{FRED_CSV_URL}?{query}")
            result.update(parse_fred_csv(content, batch, target_date))
        return result
