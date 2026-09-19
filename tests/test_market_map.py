from datetime import date

import pandas as pd

from arc_market.market_map import market_map_metrics
from arc_market.models import MarketMapInput, MarketProfile, UniverseSnapshot


def test_market_map_should_merge_duplicate_company_share_classes() -> None:
    index = pd.to_datetime(["2026-09-17", "2026-09-18"])
    prices = pd.DataFrame(
        {"GOOG": [100, 102], "GOOGL": [100, 104], "AAPL": [100, 101]},
        index=index,
    )
    universe = UniverseSnapshot(
        ("GOOG", "GOOGL", "AAPL"),
        date(2026, 9, 18),
        "wikipedia",
        {"GOOGL": "Alphabet", "AAPL": "Apple"},
        {"GOOGL": "Communication Services", "AAPL": "Information Technology"},
    )
    source = MarketMapInput(
        date(2026, 9, 18),
        universe,
        prices,
        {
            "GOOG": MarketProfile("Alphabet Class C", "Technology", 4_100),
            "GOOGL": MarketProfile("Alphabet Class A", "Technology", 4_200),
            "AAPL": MarketProfile("Apple", "Technology", 4_800),
        },
    )

    result = market_map_metrics(source)
    members = result["members"]

    assert isinstance(members, list)
    assert [item["ticker"] for item in members] == ["AAPL", "GOOGL"]
    assert members[1]["return1d"] == 3.0
    assert result["coveragePct"] == 100.0
