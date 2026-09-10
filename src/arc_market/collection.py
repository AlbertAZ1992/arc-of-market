"""Small orchestration layer with one required and four optional source groups."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol, TypeVar, cast

import pandas as pd

from arc_market.config import MarketConfig
from arc_market.errors import MarketDataError, MarketSourceError
from arc_market.models import (
    BreadthInput,
    CftcSnapshot,
    CollectedMarketData,
    OfrSnapshot,
    SourceStatus,
    TreasurySnapshot,
    UniverseSnapshot,
    VixSnapshot,
)


class PriceFetcher(Protocol):
    def fetch(self, symbols: Sequence[str], target_date: date) -> pd.DataFrame: ...


class UniverseFetcher(Protocol):
    def fetch(self, observed_at: date) -> dict[str, UniverseSnapshot]: ...


class FredSource(Protocol):
    def fetch(self, series_ids: Sequence[str], target_date: date) -> dict[str, pd.Series]: ...


class VixSource(Protocol):
    def fetch(self, target_date: date) -> VixSnapshot: ...


class OfrSource(Protocol):
    def fetch(self, target_date: date) -> OfrSnapshot: ...


class TreasurySource(Protocol):
    def fetch(self, target_date: date) -> TreasurySnapshot: ...


class CftcSource(Protocol):
    def fetch(self, target_date: date) -> CftcSnapshot: ...


@dataclass(frozen=True)
class FetcherDependencies:
    yahoo: PriceFetcher
    wikipedia: UniverseFetcher
    fred: FredSource
    cboe: VixSource
    ofr: OfrSource
    treasury: TreasurySource | None = None
    cftc: CftcSource | None = None


T = TypeVar("T")


def _last_date(frame: pd.DataFrame) -> date:
    value = pd.Timestamp(frame.index[-1]).date()
    return cast(date, value)


def _require_core(
    prices: pd.DataFrame, symbols: tuple[str, ...], target_date: date
) -> pd.DataFrame:
    missing = [symbol for symbol in symbols if symbol not in prices]
    if missing:
        raise MarketSourceError(f"core Yahoo prices are missing: {', '.join(missing)}")
    complete = prices.loc[:, list(symbols)].dropna(how="any").sort_index()
    if len(complete) < 252:
        raise MarketSourceError(f"core Yahoo prices have only {len(complete)} complete sessions")
    observed_date = _last_date(complete)
    if observed_date != target_date:
        raise MarketSourceError(
            f"core Yahoo prices end at {observed_date.isoformat()}; "
            f"expected {target_date.isoformat()}"
        )
    return complete


def _breadth_coverage(
    members: tuple[str, ...],
    prices: pd.DataFrame,
    market_as_of: date,
) -> float:
    eligible = 0
    for ticker in members:
        if ticker not in prices:
            continue
        series = pd.to_numeric(prices[ticker], errors="coerce").dropna()
        if len(series) >= 200 and pd.Timestamp(series.index[-1]).date() == market_as_of:
            eligible += 1
    return eligible / len(members) if members else 0


class MarketCollector:
    def __init__(
        self,
        config: MarketConfig,
        dependencies: FetcherDependencies,
        *,
        strict: bool = False,
    ) -> None:
        self._config = config
        self._dependencies = dependencies
        self._strict = strict
        self._statuses: list[SourceStatus] = []

    def _optional(self, source_id: str, fetch: Callable[[], T]) -> T | None:
        try:
            result = fetch()
        except Exception as error:
            if self._strict:
                raise MarketSourceError(f"optional source {source_id} failed") from error
            message = (
                str(error)[:240] if isinstance(error, MarketDataError) else type(error).__name__
            )
            self._statuses.append(SourceStatus(source_id, "FAILED", None, message))
            return None
        as_of = _result_as_of(result)
        as_of_text = as_of.isoformat() if isinstance(as_of, date) else None
        self._statuses.append(SourceStatus(source_id, "APPROVED", as_of_text))
        return result

    def _collect_breadth(self, target_date: date, market_as_of: date) -> dict[str, BreadthInput]:
        universes = self._optional(
            "wikipedia",
            lambda: self._dependencies.wikipedia.fetch(target_date),
        )
        if universes is None:
            return {}
        typed_universes = universes
        symbols = tuple(
            dict.fromkeys(
                ticker
                for index_id in self._config.breadth
                for ticker in typed_universes[index_id].members
            )
        )
        prices = self._optional(
            "yahoo-finance",
            lambda: self._dependencies.yahoo.fetch(symbols, market_as_of),
        )
        if prices is None:
            return {}
        typed_prices = prices
        result = {}
        for index_id, definition in self._config.breadth.items():
            universe = typed_universes[index_id]
            coverage = _breadth_coverage(universe.members, typed_prices, market_as_of)
            if coverage < definition.minimum_coverage:
                message = f"{index_id} breadth coverage {coverage:.1%} is below minimum"
                if self._strict:
                    raise MarketSourceError(message)
                self._statuses.append(SourceStatus("yahoo-finance", "FAILED", None, message))
                continue
            result[index_id] = BreadthInput(universe, typed_prices)
        return result

    def collect(self, target_date: date) -> CollectedMarketData:
        self._statuses = []
        core = self._dependencies.yahoo.fetch(self._config.core_symbols, target_date)
        core = _require_core(core, self._config.core_symbols, target_date)
        market_as_of = _last_date(core)
        self._statuses.append(SourceStatus("yahoo-finance", "APPROVED", market_as_of.isoformat()))
        breadth = self._collect_breadth(target_date, market_as_of)
        fred_ids = tuple(definition.series_id for definition in self._config.fred_series.values())
        fred = self._optional("fred", lambda: self._dependencies.fred.fetch(fred_ids, market_as_of))
        vix = self._optional("cboe", lambda: self._dependencies.cboe.fetch(market_as_of))
        ofr = self._optional("ofr", lambda: self._dependencies.ofr.fetch(market_as_of))
        cftc = None
        cftc_source = self._dependencies.cftc
        if cftc_source is not None:
            cftc = self._optional("cftc", lambda: cftc_source.fetch(market_as_of))
        treasury = None
        treasury_source = self._dependencies.treasury
        if treasury_source is not None:
            treasury = self._optional(
                "us-treasury",
                lambda: treasury_source.fetch(market_as_of),
            )
        return CollectedMarketData(
            market_as_of=market_as_of,
            core_prices=core,
            breadth=breadth,
            fred_series=fred,
            vix=vix,
            ofr=ofr,
            source_status=tuple(self._statuses),
            treasury=treasury,
            cftc=cftc,
        )


def _result_as_of(result: object) -> date | None:
    as_of = getattr(result, "as_of", None)
    if isinstance(as_of, date):
        return as_of
    if isinstance(result, pd.DataFrame) and not result.empty:
        return _last_date(result)
    if isinstance(result, dict):
        dates: list[date] = []
        for value in result.values():
            observed = getattr(value, "observed_at", None)
            if isinstance(observed, date):
                dates.append(observed)
            elif isinstance(value, pd.Series) and not value.empty:
                dates.append(cast(date, pd.Timestamp(value.index[-1]).date()))
        return max(dates) if dates else None
    return None
