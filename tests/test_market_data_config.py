import json
from pathlib import Path

import pytest

from arc_market.config import load_market_config
from arc_market.errors import MarketConfigError


def test_market_config_should_define_the_minimum_launch_universe() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))

    assert tuple(config.benchmarks.values()) == ("SPY", "QQQ", "DIA", "IWM")
    assert config.style.value_ticker == "VTV"
    assert config.style.growth_ticker == "QQQ"
    assert config.style.lookback_sessions == 35
    assert config.cycle.semiconductor_ticker == "SMH"
    assert config.cycle.benchmark_ticker == "QQQ"
    assert tuple(config.sectors) == (
        "XLB",
        "XLC",
        "XLE",
        "XLF",
        "XLI",
        "XLK",
        "XLP",
        "XLRE",
        "XLU",
        "XLV",
        "XLY",
    )
    assert tuple(config.mega7) == (
        "AAPL",
        "MSFT",
        "AMZN",
        "GOOGL",
        "META",
        "NVDA",
        "TSLA",
    )
    assert "themes" not in config.raw


def test_market_config_should_exclude_ice_bofa_and_publish_cftc() -> None:
    config = load_market_config(Path("config/market-data-v2.json"))

    assert "creditHyOas" not in config.fred_series
    assert "ice-data-indices" not in config.sources
    assert config.sources["cftc"]["publishPolicy"] == "public-domain-time-series"


def test_market_config_should_fail_closed_on_unknown_root_field(tmp_path: Path) -> None:
    source = json.loads(Path("config/market-data-v2.json").read_text(encoding="utf-8"))
    source["unknown"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(MarketConfigError, match="root fields"):
        load_market_config(path)


def test_market_config_should_fail_closed_on_ice_bofa_series(tmp_path: Path) -> None:
    source = json.loads(Path("config/market-data-v2.json").read_text(encoding="utf-8"))
    source["fredSeries"]["creditHyOas"] = {
        "seriesId": "BAMLH0A0HYM2",
        "unit": "percentage_points",
        "transform": "component",
    }
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(MarketConfigError, match="not approved for public release"):
        load_market_config(path)
