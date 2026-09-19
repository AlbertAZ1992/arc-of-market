"""Build a compact market-cap map from public constituent profiles and prices."""

import pandas as pd

from arc_market.models import MarketMapInput

_SECTOR_NAMES = {
    "Basic Materials": "Materials",
    "Finance": "Financials",
    "Technology": "Information Technology",
    "Telecommunications": "Communication Services",
}
_SHARE_CLASS_ALIASES = {"FOX": "FOXA", "GOOG": "GOOGL", "NWS": "NWSA"}


def _daily_return(prices: pd.DataFrame, ticker: str, as_of: object) -> float | None:
    if ticker not in prices:
        return None
    series = pd.to_numeric(prices[ticker], errors="coerce").dropna().sort_index()
    if len(series) < 2 or pd.Timestamp(series.index[-1]).date() != as_of:
        return None
    previous = float(series.iloc[-2])
    if previous <= 0:
        return None
    return (float(series.iloc[-1]) / previous - 1) * 100


def market_map_metrics(source: MarketMapInput) -> dict[str, object]:
    grouped: dict[str, list[tuple[str, float]]] = {}
    for ticker in source.universe.members:
        profile = source.profiles.get(ticker)
        daily_return = _daily_return(source.prices, ticker, source.as_of)
        if profile is None or daily_return is None:
            continue
        canonical = _SHARE_CLASS_ALIASES.get(ticker, ticker)
        grouped.setdefault(canonical, []).append((ticker, daily_return))
    candidates: list[tuple[str, str, str, float, float]] = []
    for ticker, share_classes in grouped.items():
        profiles = [source.profiles[item[0]] for item in share_classes]
        profile = max(profiles, key=lambda item: item.market_cap)
        name = (source.universe.names or {}).get(ticker, profile.name)
        sector = (source.universe.sectors or {}).get(ticker, profile.sector)
        daily_return = sum(item[1] for item in share_classes) / len(share_classes)
        candidates.append(
            (ticker, name, _SECTOR_NAMES.get(sector, sector), profile.market_cap, daily_return)
        )
    matched_tickers = sum(len(items) for items in grouped.values())
    total_market_cap = sum(item[3] for item in candidates)
    members = [
        {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "marketCapWeightPct": round(market_cap / total_market_cap * 100, 6),
            "return1d": round(daily_return, 4),
        }
        for ticker, name, sector, market_cap, daily_return in sorted(
            candidates,
            key=lambda item: item[3],
            reverse=True,
        )
        if total_market_cap > 0
    ]
    coverage = matched_tickers / len(source.universe.members) * 100
    return {
        "universe": "sp500-current-members",
        "weighting": "current-market-cap",
        "asOf": source.as_of.isoformat(),
        "coveragePct": round(coverage, 2),
        "members": members,
    }
