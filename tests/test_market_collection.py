from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from arc_market.collection import FetcherDependencies, MarketCollector, _require_core
from arc_market.config import load_market_config
from arc_market.errors import MarketSourceError
from arc_market.models import OfrSnapshot, TreasurySnapshot, UniverseSnapshot, VixSnapshot


def price_frame(symbols: tuple[str, ...], *, periods: int = 270) -> pd.DataFrame:
    index = pd.bdate_range(end="2026-08-28", periods=periods)
    return pd.DataFrame(
        {
            symbol: [100 + offset + step for step in range(periods)]
            for offset, symbol in enumerate(symbols)
        },
        index=index,
        dtype="float64",
    )


class FakeYahoo:
    def __init__(self, core_symbols: tuple[str, ...]) -> None:
        self.core_symbols = core_symbols

    def fetch(self, symbols: tuple[str, ...], _target: date) -> pd.DataFrame:
        if symbols == self.core_symbols:
            return price_frame(symbols)
        return price_frame(symbols, periods=220)


class FakeUniverses:
    def fetch(self, observed_at: date) -> dict[str, UniverseSnapshot]:
        members = ("AAA", "BBB")
        return {
            index_id: UniverseSnapshot(members, observed_at, "wikipedia")
            for index_id in ("sp500", "nasdaq100", "dow30")
        }


class FakeFred:
    def fetch(self, series_ids: tuple[str, ...], _target: date) -> dict[str, pd.Series]:
        index = pd.date_range(end="2026-08-01", periods=18, freq="MS")
        return {
            series_id: pd.Series(range(100, 118), index=index, dtype="float64")
            for series_id in series_ids
        }


class FakeVix:
    def fetch(self, _target: date) -> VixSnapshot:
        return VixSnapshot(date(2026, 8, 28), 18.4)


class FakeOfr:
    def fetch(self, _target: date) -> OfrSnapshot:
        return OfrSnapshot(date(2026, 8, 28), 0.5, {"credit": 0.1}, {"us": 0.3})


class FakeTreasury:
    def fetch(self, _target: date) -> TreasurySnapshot:
        return TreasurySnapshot(date(2026, 8, 28), 4.2, 4.7, 3.0, 1.0, 7.0)


class FailingFred:
    def fetch(self, _series_ids: tuple[str, ...], _target: date) -> dict[str, pd.Series]:
        raise MarketSourceError("FRED unavailable")


class LeakingFred:
    def fetch(self, _series_ids: tuple[str, ...], _target: date) -> dict[str, pd.Series]:
        raise RuntimeError("upstream response contained private connection metadata")


def dependencies(
    config_symbols: tuple[str, ...], *, fred: object | None = None
) -> FetcherDependencies:
    return FetcherDependencies(
        yahoo=FakeYahoo(config_symbols),
        wikipedia=FakeUniverses(),
        fred=fred or FakeFred(),
        cboe=FakeVix(),
        ofr=FakeOfr(),
        treasury=FakeTreasury(),
    )


def test_collector_should_fetch_core_once_and_build_optional_breadth() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))
    collector = MarketCollector(config, dependencies(config.core_symbols))

    result = collector.collect(date(2026, 8, 28))

    assert result.market_as_of == date(2026, 8, 28)
    assert set(result.core_prices) == set(config.core_symbols)
    assert set(result.breadth) == {"sp500", "nasdaq100", "dow30"}
    assert result.treasury is not None
    status_as_of = {status.source_id: status.as_of for status in result.source_status}
    assert status_as_of["wikipedia"] == "2026-08-28"
    assert status_as_of["us-treasury"] == "2026-08-28"
    assert all(status.status == "APPROVED" for status in result.source_status)


def test_collector_should_degrade_when_optional_source_fails() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))
    collector = MarketCollector(
        config,
        dependencies(config.core_symbols, fred=FailingFred()),
    )

    result = collector.collect(date(2026, 8, 28))

    assert result.fred_series is None
    assert any(
        status.source_id == "fred" and status.status == "FAILED" for status in result.source_status
    )


def test_collector_should_fail_optional_source_in_strict_mode() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))
    collector = MarketCollector(
        config,
        dependencies(config.core_symbols, fred=FailingFred()),
        strict=True,
    )

    with pytest.raises(MarketSourceError, match="fred"):
        collector.collect(date(2026, 8, 28))


def test_collector_should_not_publish_uncontrolled_exception_messages() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))
    collector = MarketCollector(
        config,
        dependencies(config.core_symbols, fred=LeakingFred()),
    )

    result = collector.collect(date(2026, 8, 28))

    failure = next(status for status in result.source_status if status.source_id == "fred")
    assert failure.message == "RuntimeError"


def test_core_prices_should_require_enough_history_for_52_week_metrics() -> None:
    prices = price_frame(("SPY", "QQQ"), periods=251)

    with pytest.raises(MarketSourceError, match="251 complete sessions"):
        _require_core(prices, ("SPY", "QQQ"), date(2026, 8, 28))


def test_core_prices_should_reject_a_stale_latest_session() -> None:
    prices = price_frame(("SPY", "QQQ"))

    with pytest.raises(
        MarketSourceError,
        match="core Yahoo prices end at 2026-08-28; expected 2026-08-31",
    ):
        _require_core(prices, ("SPY", "QQQ"), date(2026, 8, 31))
