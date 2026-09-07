"""Build the public signal snapshot without changing the ROC35 calculation."""

from collections.abc import Mapping
from datetime import date

from arc_market.scores import (
    cycle_score,
    market_signal,
    participation_score,
    risk_score,
    trend_score,
)


def _style(data: Mapping[str, object]) -> dict[str, object]:
    raw = data.get("style")
    style = raw if isinstance(raw, dict) else {}
    value = style.get("value")
    direction = style.get("direction")
    if not isinstance(value, int | float) or isinstance(value, bool):
        state = "UNAVAILABLE"
    elif value > 0:
        state = "VALUE_LEADING"
    elif value < 0:
        state = "GROWTH_LEADING"
    else:
        state = "NEUTRAL"
    return {
        "indicatorId": "style",
        "engineVersion": "1.0.0",
        "state": state,
        "roc35": value,
        "direction": direction,
    }


def build_indicator_snapshot(data: Mapping[str, object], *, as_of: date) -> dict[str, object]:
    participation = participation_score(data)
    observations = {
        "trend": trend_score(data),
        "participation": participation,
        "style": _style(data),
        "cycle": cycle_score(data),
    }
    risk_window = risk_score(data, participation)
    return {
        "asOf": as_of.isoformat(),
        "observations": observations,
        "riskWindow": risk_window,
        "marketSignal": market_signal(observations, risk_window),
    }
