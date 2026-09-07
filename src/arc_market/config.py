"""Fail-closed loading for the compact market-data catalog."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from arc_market.errors import MarketConfigError

_ROOT_FIELDS = {
    "schemaVersion",
    "methodologyVersion",
    "priceGroups",
    "style",
    "cycle",
    "sectorLabels",
    "mega7",
    "breadth",
    "fredSeries",
    "sources",
}
_TICKER = re.compile(r"^[A-Z0-9.-]{1,12}$")
_FORBIDDEN_PUBLIC_FRED_SERIES = {"BAMLH0A0HYM2"}


@dataclass(frozen=True)
class ParticipationPair:
    pair_id: str
    equal_weight_ticker: str
    cap_weight_ticker: str


@dataclass(frozen=True)
class BreadthDefinition:
    source_id: str
    minimum_coverage: float


@dataclass(frozen=True)
class StyleDefinition:
    value_ticker: str
    growth_ticker: str
    lookback_sessions: int


@dataclass(frozen=True)
class CycleDefinition:
    semiconductor_ticker: str
    benchmark_ticker: str


@dataclass(frozen=True)
class FredDefinition:
    series_id: str
    unit: str
    transform: str


@dataclass(frozen=True)
class MarketConfig:
    methodology_version: str
    benchmarks: dict[str, str]
    participation: tuple[ParticipationPair, ...]
    style: StyleDefinition
    cycle: CycleDefinition
    sectors: dict[str, str]
    mega7: tuple[str, ...]
    breadth: dict[str, BreadthDefinition]
    fred_series: dict[str, FredDefinition]
    sources: dict[str, dict[str, str]]
    raw: dict[str, Any]

    @property
    def core_symbols(self) -> tuple[str, ...]:
        symbols = list(self.benchmarks.values())
        for pair in self.participation:
            symbols.extend((pair.equal_weight_ticker, pair.cap_weight_ticker))
        symbols.extend((self.style.value_ticker, self.style.growth_ticker))
        symbols.extend((self.cycle.semiconductor_ticker, self.cycle.benchmark_ticker))
        symbols.extend(self.sectors)
        symbols.extend(self.mega7)
        return tuple(dict.fromkeys(symbols))


def _ticker(value: object, field: str) -> str:
    if not isinstance(value, str) or _TICKER.fullmatch(value) is None:
        raise MarketConfigError(f"{field} must be a valid ticker")
    return value


def _string_map(value: object, field: str) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise MarketConfigError(f"{field} must be a non-empty object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str) or not item:
            raise MarketConfigError(f"{field} entries must be non-empty strings")
        result[key] = item
    return result


def _pairs(value: object) -> tuple[ParticipationPair, ...]:
    if not isinstance(value, list) or not value:
        raise MarketConfigError("priceGroups.participation must be a non-empty array")
    pairs: list[ParticipationPair] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "pairId",
            "equalWeightTicker",
            "capWeightTicker",
        }:
            raise MarketConfigError("participation pair fields are invalid")
        pair = cast(dict[str, object], item)
        pair_id = pair["pairId"]
        if not isinstance(pair_id, str) or not pair_id:
            raise MarketConfigError("participation pairId must be a non-empty string")
        pairs.append(
            ParticipationPair(
                pair_id,
                _ticker(pair["equalWeightTicker"], "equalWeightTicker"),
                _ticker(pair["capWeightTicker"], "capWeightTicker"),
            )
        )
    return tuple(pairs)


def _breadth(value: object) -> dict[str, BreadthDefinition]:
    if not isinstance(value, dict) or set(value) != {"sp500", "nasdaq100", "dow30"}:
        raise MarketConfigError("breadth definitions are invalid")
    result: dict[str, BreadthDefinition] = {}
    typed = cast(dict[str, object], value)
    for index_id, item in typed.items():
        if not isinstance(item, dict) or set(item) != {"sourceId", "minimumCoverage"}:
            raise MarketConfigError(f"breadth {index_id} fields are invalid")
        definition = cast(dict[str, object], item)
        source_id = definition["sourceId"]
        coverage = definition["minimumCoverage"]
        if not isinstance(source_id, str) or not source_id:
            raise MarketConfigError(f"breadth {index_id} sourceId is invalid")
        if not isinstance(coverage, int | float) or not 0.5 <= float(coverage) <= 1:
            raise MarketConfigError(f"breadth {index_id} minimumCoverage is invalid")
        result[index_id] = BreadthDefinition(source_id, float(coverage))
    return result


def _style(value: object) -> StyleDefinition:
    if not isinstance(value, dict) or set(value) != {
        "valueTicker",
        "growthTicker",
        "lookbackSessions",
    }:
        raise MarketConfigError("style fields are invalid")
    typed = cast(dict[str, object], value)
    lookback = typed["lookbackSessions"]
    if not isinstance(lookback, int) or not 20 <= lookback <= 252:
        raise MarketConfigError("style lookbackSessions is invalid")
    return StyleDefinition(
        _ticker(typed["valueTicker"], "style.valueTicker"),
        _ticker(typed["growthTicker"], "style.growthTicker"),
        lookback,
    )


def _cycle(value: object) -> CycleDefinition:
    if not isinstance(value, dict) or set(value) != {
        "semiconductorTicker",
        "benchmarkTicker",
    }:
        raise MarketConfigError("cycle fields are invalid")
    typed = cast(dict[str, object], value)
    return CycleDefinition(
        _ticker(typed["semiconductorTicker"], "cycle.semiconductorTicker"),
        _ticker(typed["benchmarkTicker"], "cycle.benchmarkTicker"),
    )


def _fred(value: object) -> dict[str, FredDefinition]:
    if not isinstance(value, dict) or not value:
        raise MarketConfigError("fredSeries must be a non-empty object")
    result: dict[str, FredDefinition] = {}
    allowed_transforms = {"latest", "yoy", "change", "millions_to_trillions", "component"}
    typed = cast(dict[str, object], value)
    for key, item in typed.items():
        if not isinstance(item, dict) or set(item) != {"seriesId", "unit", "transform"}:
            raise MarketConfigError(f"FRED definition {key} fields are invalid")
        definition = cast(dict[str, object], item)
        series_id = definition["seriesId"]
        unit = definition["unit"]
        transform = definition["transform"]
        if not all(isinstance(part, str) and part for part in (series_id, unit, transform)):
            raise MarketConfigError(f"FRED definition {key} values are invalid")
        if transform not in allowed_transforms:
            raise MarketConfigError(f"FRED definition {key} transform is invalid")
        if series_id in _FORBIDDEN_PUBLIC_FRED_SERIES:
            raise MarketConfigError(f"FRED definition {key} is not approved for public release")
        result[key] = FredDefinition(
            cast(str, series_id),
            cast(str, unit),
            cast(str, transform),
        )
    return result


def _load_document(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MarketConfigError(f"cannot load market-data config: {path}") from error
    if not isinstance(value, dict) or set(value) != _ROOT_FIELDS:
        raise MarketConfigError("market-data config root fields are invalid")
    return cast(dict[str, Any], value)


def load_market_config(path: Path) -> MarketConfig:
    document = _load_document(path)
    price_groups = document["priceGroups"]
    if not isinstance(price_groups, dict) or set(price_groups) != {"benchmarks", "participation"}:
        raise MarketConfigError("priceGroups fields are invalid")
    benchmarks = _string_map(price_groups["benchmarks"], "priceGroups.benchmarks")
    benchmarks = {key: _ticker(value, key) for key, value in benchmarks.items()}
    sectors = _string_map(document["sectorLabels"], "sectorLabels")
    sectors = {_ticker(key, "sector ticker"): label for key, label in sectors.items()}
    mega7_value = document["mega7"]
    if not isinstance(mega7_value, list) or len(mega7_value) != 7:
        raise MarketConfigError("mega7 must contain exactly seven tickers")
    mega7 = tuple(_ticker(item, "mega7") for item in mega7_value)
    methodology = document["methodologyVersion"]
    if document["schemaVersion"] != "2.0" or not isinstance(methodology, str):
        raise MarketConfigError("market-data config version is invalid")
    sources = document["sources"]
    if not isinstance(sources, dict):
        raise MarketConfigError("sources must be an object")
    return MarketConfig(
        methodology,
        benchmarks,
        _pairs(price_groups["participation"]),
        _style(document["style"]),
        _cycle(document["cycle"]),
        sectors,
        mega7,
        _breadth(document["breadth"]),
        _fred(document["fredSeries"]),
        cast(dict[str, dict[str, str]], sources),
        document,
    )
