import pandas as pd
from scripts.macro_indicators import equity_allocation_payload, equity_allocation_share


def test_equity_allocation_share_aligns_components_and_uses_total_value() -> None:
    dates = pd.to_datetime(["2025-03-31", "2025-06-30"])
    observations = {
        "EQ1": pd.Series([20.0, 30.0], index=dates),
        "EQ2": pd.Series([10.0, 10.0], index=dates),
        "DEBT1": pd.Series([70.0, 60.0], index=dates),
    }

    result = equity_allocation_share(observations, ("EQ1", "EQ2"), ("DEBT1",))

    assert result.to_dict() == {
        pd.Timestamp("2025-03-31"): 0.3,
        pd.Timestamp("2025-06-30"): 0.4,
    }


def test_equity_allocation_payload_records_formula_and_percentile() -> None:
    values = pd.Series(
        [0.2, 0.4, 0.3],
        index=pd.to_datetime(["2024-09-30", "2024-12-31", "2025-03-31"]),
    )

    payload = equity_allocation_payload(values, ("EQ", "DEBT"))

    assert payload["meta"]["current_value"] == 0.3
    assert payload["meta"]["current_percentile"] == 66.7
    assert payload["meta"]["as_of"] == "2025-03-31"
    assert payload["values"] == [0.2, 0.4, 0.3]
