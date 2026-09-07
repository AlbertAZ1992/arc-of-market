"""Transparent multi-factor scores for the four market observation planes."""

import math
from collections.abc import Mapping, Sequence
from typing import cast

_ENGINE_VERSION = "2.0.0"


def _mapping(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else {}


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast(Mapping[str, object], row) for row in value if isinstance(row, dict)]


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if not math.isfinite(float(value)):
        return None
    return float(value)


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _component(
    component_id: str,
    value: object,
    score: float,
    weight: float,
) -> dict[str, object]:
    normalized = round(_clamp(score), 2)
    return {
        "componentId": component_id,
        "value": value,
        "score": normalized,
        "weight": weight,
        "contribution": round(normalized * weight, 2),
    }


def _summary(components: Sequence[dict[str, object]]) -> tuple[float | None, float]:
    weight = sum(_number(item["weight"]) or 0.0 for item in components)
    if weight <= 0:
        return None, 0.0
    contribution = sum(_number(item["contribution"]) or 0.0 for item in components)
    return round(contribution / weight, 2), round(min(weight, 1.0), 2)


def _state(score: float | None, confidence: float, upper: float, lower: float) -> str:
    if score is None or confidence < 0.5:
        return "UNAVAILABLE"
    if score >= upper:
        return "POSITIVE"
    if score <= lower:
        return "NEGATIVE"
    return "NEUTRAL"


def _structure_score(above_short: object, above_long: object) -> float | None:
    if not isinstance(above_short, bool) or not isinstance(above_long, bool):
        return None
    if above_short and above_long:
        return 100.0
    if above_long:
        return 65.0
    if above_short:
        return 35.0
    return 0.0


def trend_score(data: Mapping[str, object]) -> dict[str, object]:
    snapshots = {str(row.get("ticker")): row for row in _rows(data.get("trendSnapshot"))}
    overview = {str(row.get("proxyTicker")): row for row in _rows(data.get("marketOverview"))}
    components: list[dict[str, object]] = []
    for ticker in ("SPY", "QQQ"):
        snapshot = snapshots.get(ticker, {})
        market = overview.get(ticker, {})
        short = _structure_score(snapshot.get("aboveMa20"), snapshot.get("aboveMa50"))
        long = _structure_score(market.get("aboveMa50"), market.get("aboveMa200"))
        if short is not None:
            components.append(_component(f"{ticker.lower()}-short-trend", short, short, 0.15))
        if long is not None:
            components.append(_component(f"{ticker.lower()}-long-trend", long, long, 0.20))
        monthly_return = _number(market.get("return1m"))
        volatility = _number(market.get("realizedVol20d"))
        if monthly_return is not None and volatility is not None and volatility > 0:
            risk_adjusted = monthly_return / (volatility / math.sqrt(12))
            components.append(
                _component(
                    f"{ticker.lower()}-risk-adjusted-momentum",
                    round(risk_adjusted, 4),
                    50 + 25 * risk_adjusted,
                    0.15,
                )
            )
    score, confidence = _summary(components)
    state = _state(score, confidence, 65, 35)
    return {
        "indicatorId": "trend",
        "engineVersion": _ENGINE_VERSION,
        "state": {"POSITIVE": "BULLISH", "NEGATIVE": "BEARISH"}.get(state, state),
        "score": score,
        "confidence": confidence,
        "components": components,
        "spyAboveMa20": snapshots.get("SPY", {}).get("aboveMa20"),
        "spyAboveMa50": snapshots.get("SPY", {}).get("aboveMa50"),
        "qqqAboveMa20": snapshots.get("QQQ", {}).get("aboveMa20"),
        "qqqAboveMa50": snapshots.get("QQQ", {}).get("aboveMa50"),
    }


def _breadth_components(data: Mapping[str, object]) -> list[dict[str, object]]:
    components: list[dict[str, object]] = []
    rows = {str(row.get("indexId")): row for row in _rows(data.get("breadth"))}
    for index_id in ("sp500", "nasdaq100"):
        row = rows.get(index_id, {})
        for field, suffix in (("pctAboveMa50", "ma50"), ("pctAboveMa200", "ma200")):
            value = _number(row.get(field))
            if value is not None:
                components.append(_component(f"{index_id}-{suffix}-breadth", value, value, 0.15))
    return components


def participation_score(data: Mapping[str, object]) -> dict[str, object]:
    components = _breadth_components(data)
    rows = {str(row.get("pairId")): row for row in _rows(data.get("participation"))}
    for pair_id in ("sp500_equal_weight", "nasdaq100_equal_weight"):
        row = rows.get(pair_id, {})
        relative = _number(row.get("relativeReturn1m"))
        above = row.get("ratioAboveMa50")
        if relative is not None:
            components.append(
                _component(f"{pair_id}-relative-1m", relative, 50 + 10 * relative, 0.10)
            )
        if isinstance(above, bool):
            components.append(_component(f"{pair_id}-ratio-ma50", above, 70 if above else 30, 0.10))
    score, confidence = _summary(components)
    state = _state(score, confidence, 60, 40)
    breadth_states = {
        str(row.get("indexId")): str(row.get("breadthState")) for row in _rows(data.get("breadth"))
    }
    ratio_states = {
        str(row.get("pairId")): str(row.get("participationState"))
        for row in _rows(data.get("participation"))
    }
    return {
        "indicatorId": "participation",
        "engineVersion": _ENGINE_VERSION,
        "state": {
            "POSITIVE": "BROAD",
            "NEUTRAL": "MIXED",
            "NEGATIVE": "NARROW",
        }.get(state, state),
        "score": score,
        "confidence": confidence,
        "components": components,
        "breadthStates": breadth_states,
        "ratioStates": ratio_states,
    }


def _sector_cycle_components(data: Mapping[str, object]) -> list[dict[str, object]]:
    sectors = {str(row.get("ticker")): row for row in _rows(data.get("sectors"))}
    cyclicals = [
        _number(sectors.get(ticker, {}).get("relative1m")) for ticker in ("XLY", "XLI", "XLF")
    ]
    defensives = [
        _number(sectors.get(ticker, {}).get("relative1m")) for ticker in ("XLP", "XLU", "XLV")
    ]
    valid_cyclicals = [value for value in cyclicals if value is not None]
    valid_defensives = [value for value in defensives if value is not None]
    components: list[dict[str, object]] = []
    if len(valid_cyclicals) == 3 and len(valid_defensives) == 3:
        spread = sum(valid_cyclicals) / 3 - sum(valid_defensives) / 3
        components.append(
            _component("cyclical-defensive-spread", round(spread, 4), 50 + 10 * spread, 0.25)
        )
    returns = [_number(row.get("return1m")) for row in sectors.values()]
    valid_returns = [value for value in returns if value is not None]
    if valid_returns:
        diffusion = sum(value > 0 for value in valid_returns) / len(valid_returns) * 100
        components.append(
            _component("sector-positive-diffusion", round(diffusion, 2), diffusion, 0.15)
        )
    return components


def cycle_score(data: Mapping[str, object]) -> dict[str, object]:
    components = _sector_cycle_components(data)
    pulse = _mapping(data.get("semiconductorPulse"))
    for field, suffix, weight in (
        ("relativeReturn1w", "1w", 0.15),
        ("relativeReturn1m", "1m", 0.25),
    ):
        value = _number(pulse.get(field))
        if value is not None:
            components.append(
                _component(f"semiconductor-relative-{suffix}", value, 50 + 10 * value, weight)
            )
    overview = {str(row.get("proxyTicker")): row for row in _rows(data.get("marketOverview"))}
    small = _number(overview.get("IWM", {}).get("return1m"))
    large = _number(overview.get("SPY", {}).get("return1m"))
    if small is not None and large is not None:
        relative = small - large
        components.append(
            _component("small-cap-relative-1m", round(relative, 4), 50 + 10 * relative, 0.20)
        )
    score, confidence = _summary(components)
    state = _state(score, confidence, 60, 40)
    return {
        "indicatorId": "cycle",
        "engineVersion": _ENGINE_VERSION,
        "state": {
            "POSITIVE": "LEADING",
            "NEUTRAL": "MIXED",
            "NEGATIVE": "LAGGING",
        }.get(state, state),
        "score": score,
        "confidence": confidence,
        "components": components,
        "semiconductorRelative1w": _number(pulse.get("relativeReturn1w")),
        "semiconductorRelative1m": _number(pulse.get("relativeReturn1m")),
    }


def _risk_state(score: float | None, confidence: float) -> str:
    if score is None or confidence < 0.5:
        return "UNAVAILABLE"
    if score <= 30:
        return "CALM"
    if score <= 55:
        return "NORMAL"
    if score <= 75:
        return "ELEVATED"
    return "STRESS"


def risk_score(
    data: Mapping[str, object],
    participation: Mapping[str, object],
) -> dict[str, object]:
    risk = _mapping(data.get("risk"))
    treasury = _mapping(data.get("treasuryCurve"))
    stress = _mapping(data.get("financialStress"))
    components: list[dict[str, object]] = []
    values = (
        ("vix-level", _number(risk.get("vixValue")), 0.25, lambda value: (value - 12) / 16 * 100),
        ("vix-change-1d", _number(risk.get("vixChange1dPct")), 0.10, lambda value: 50 + 5 * value),
        (
            "drawdown",
            _number(risk.get("currentDrawdown")),
            0.15,
            lambda value: abs(min(value, 0)) / 15 * 100,
        ),
        (
            "rates-shock-3d",
            _number(treasury.get("treasury10yChange3dBp")),
            0.10,
            lambda value: 50 + 2 * value,
        ),
        ("financial-stress", _number(stress.get("value")), 0.10, lambda value: 50 + 25 * value),
    )
    for component_id, value, weight, normalize in values:
        if value is not None:
            components.append(_component(component_id, value, normalize(value), weight))
    vol20 = _number(risk.get("realizedVol20d"))
    vol60 = _number(risk.get("realizedVol60d"))
    if vol20 is not None and vol60 is not None and vol60 > 0:
        ratio = vol20 / vol60
        components.append(
            _component("volatility-acceleration", round(ratio, 4), 50 + 100 * (ratio - 1), 0.20)
        )
    participation_value = _number(participation.get("score"))
    if participation_value is not None:
        components.append(
            _component("participation-stress", participation_value, 100 - participation_value, 0.10)
        )
    score, confidence = _summary(components)
    state = _risk_state(score, confidence)
    flags = [
        str(item["componentId"]).upper().replace("-", "_")
        for item in components
        if (_number(item["score"]) or 0.0) >= 70
    ]
    return {
        "indicatorId": "risk-window",
        "engineVersion": _ENGINE_VERSION,
        "state": {"CALM": "OPEN", "NORMAL": "OPEN", "ELEVATED": "CAUTION", "STRESS": "CLOSED"}.get(
            state, state
        ),
        "riskScore": score,
        "confidence": confidence,
        "components": components,
        "flags": flags,
        "thresholds": {"cautionRiskScore": 55, "closedRiskScore": 75},
    }


def market_signal(
    observations: Mapping[str, Mapping[str, object]],
    risk_window: Mapping[str, object],
) -> dict[str, object]:
    weights = {"trend": 0.35, "participation": 0.30, "cycle": 0.20}
    available: list[tuple[float, float, float]] = []
    for key, weight in weights.items():
        score = _number(observations[key].get("score"))
        confidence = _number(observations[key].get("confidence"))
        if score is not None and confidence is not None:
            available.append((score, weight, confidence))
    risk = _number(risk_window.get("riskScore"))
    risk_confidence = _number(risk_window.get("confidence"))
    if risk is not None and risk_confidence is not None:
        available.append((100 - risk, 0.15, risk_confidence))
    total_weight = sum(weight for _score, weight, _confidence in available)
    score = (
        None
        if total_weight == 0
        else round(
            sum(value * weight for value, weight, _confidence in available) / total_weight, 2
        )
    )
    confidence = round(sum(weight * value for _score, weight, value in available), 2)
    if score is None or confidence < 0.65:
        state = "UNAVAILABLE"
    elif risk is not None and risk >= 75 or score < 35:
        state = "DEFENSIVE"
    elif score >= 65 and (risk is None or risk < 55):
        state = "RISK_ON"
    else:
        state = "WATCH"
    return {
        "signalId": "market-regime",
        "engineVersion": _ENGINE_VERSION,
        "state": state,
        "score": score,
        "confidence": confidence,
        "observationStates": {key: str(value["state"]) for key, value in observations.items()},
        "riskWindowState": str(risk_window["state"]),
        "styleIncludedInScore": False,
    }
