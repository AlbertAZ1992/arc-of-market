import json
import math
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pandas as pd
import pytest
from scripts import harvest


def test_pin_rejects_non_finite_values(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(harvest, "DATA", tmp_path)
    monkeypatch.setattr(
        harvest,
        "dataset_record",
        lambda _name: {
            "group": "test",
            "source_ids": ["test"],
            "access": {"public": False, "subscriber": False},
            "derived_output": "not-applicable",
            "status": "internal-operational",
        },
    )

    with pytest.raises(ValueError, match="Out of range float values"):
        harvest.pin("invalid.json", {"value": math.nan})


def test_fetch_history_uses_yfinance_managed_session(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []
    index = pd.date_range("2025-01-01", periods=101, freq="D", tz="America/New_York")
    frame = pd.DataFrame({"Close": range(101)}, index=index)

    class FakeTicker:
        def __init__(self, symbol: str, **kwargs) -> None:
            calls.append((symbol, kwargs))

        def history(self, **kwargs) -> pd.DataFrame:
            assert kwargs == {"period": "max", "auto_adjust": True}
            return frame

    monkeypatch.setattr(harvest.yf, "Ticker", FakeTicker)
    harvest._SOURCE_TRACE.clear()

    result = harvest.fetch_history("SPY", retries=1)

    assert calls == [("SPY", {})]
    assert pd.DatetimeIndex(result.index).tz is None
    assert harvest._SOURCE_TRACE["yahoo:SPY"].endswith("2025-04-11)")


def test_fetch_history_warns_when_latest_yahoo_row_has_no_close(monkeypatch) -> None:
    index = pd.date_range("2025-01-01", periods=102, freq="D", tz="America/New_York")
    frame = pd.DataFrame({"Close": [*range(101), None]}, index=index)

    class FakeTicker:
        def __init__(self, _symbol: str) -> None:
            pass

        def history(self, **_kwargs) -> pd.DataFrame:
            return frame

    monkeypatch.setattr(harvest.yf, "Ticker", FakeTicker)
    harvest._FAILURES.clear()

    result = harvest.fetch_history("SPY", retries=1)

    assert len(result) == 101
    assert harvest._FAILURES == [
        {
            "section": "source yahoo:SPY",
            "error": "latest row 2025-04-12 has no close; using 2025-04-11",
            "blocking": False,
        }
    ]


def test_fetch_history_repairs_latest_missing_yahoo_row(monkeypatch) -> None:
    index = pd.date_range("2025-01-01", periods=102, freq="D", tz="America/New_York")
    incomplete = pd.DataFrame({"Close": [*range(101), None]}, index=index)
    repaired = pd.DataFrame(
        {"Close": [100.0, 101.0], "Repaired?": [False, True]},
        index=index[-2:],
    )

    class FakeTicker:
        def __init__(self, _symbol: str) -> None:
            pass

        def history(self, **kwargs) -> pd.DataFrame:
            return repaired if kwargs.get("repair") else incomplete

    monkeypatch.setattr(harvest.yf, "Ticker", FakeTicker)
    harvest._FAILURES.clear()
    harvest._SOURCE_TRACE.clear()

    result = harvest.fetch_history("SPY", retries=1)

    assert result.iloc[-1]["Close"] == 101.0
    assert harvest._FAILURES == []
    assert "repaired=2025-04-12" in harvest._SOURCE_TRACE["yahoo:SPY"]


def test_fetch_history_repairs_when_latest_date_lags_expected(monkeypatch) -> None:
    index = pd.date_range("2025-01-01", periods=101, freq="D", tz="America/New_York")
    initial = pd.DataFrame({"Close": range(101)}, index=index)
    repaired_index = pd.DatetimeIndex([index[-1], index[-1] + pd.Timedelta(days=1)])
    repaired = pd.DataFrame(
        {"Close": [100.0, 101.0], "Repaired?": [False, True]},
        index=repaired_index,
    )

    class FakeTicker:
        def __init__(self, _symbol: str) -> None:
            pass

        def history(self, **kwargs) -> pd.DataFrame:
            return repaired if kwargs.get("repair") else initial

    monkeypatch.setattr(harvest.yf, "Ticker", FakeTicker)
    harvest._FAILURES.clear()

    result = harvest.fetch_history(
        "SPY",
        retries=1,
        expected_date=cast(pd.Timestamp, pd.Timestamp("2025-04-12")),
    )

    assert result.index[-1] == pd.Timestamp("2025-04-12")
    assert harvest._FAILURES == []


def test_drawdown_episodes_preserve_peak_trough_and_recovery_dates() -> None:
    close = pd.Series(
        [100.0, 90.0, 80.0, 101.0, 95.0],
        index=pd.date_range("2025-01-01", periods=5, freq="D"),
    )

    drawdown, episodes = harvest.drawdown_episodes(close)

    assert drawdown.iloc[2] == pytest.approx(-0.2)
    assert episodes == [
        {
            "peak": "2025-01-01",
            "trough": "2025-01-03",
            "recovery": "2025-01-04",
            "depth": -20.0,
        },
        {
            "peak": "2025-01-04",
            "trough": "2025-01-05",
            "recovery": None,
            "depth": -5.94,
        },
    ]


def test_quarterly_percent_change_uses_four_periods() -> None:
    series = pd.Series(
        [100.0, 101.0, 102.0, 103.0, 110.0],
        index=pd.date_range("2024-01-01", periods=5, freq="QS"),
    )

    result = harvest.percent_change_payload(series, lag=4)

    assert result["values"] == [10.0]


def test_percent_change_drops_zero_prior_values() -> None:
    series = pd.Series(
        [0.0, 10.0, 12.0],
        index=pd.date_range("2024-01-01", periods=3, freq="MS"),
    )

    result = harvest.percent_change_payload(series, lag=1)

    assert result["dates"] == ["2024-03-01"]
    assert result["values"] == [20.0]


def test_weekly_sampling_preserves_last_observation_date() -> None:
    series = pd.Series(
        [1.0, 2.0, 3.0],
        index=pd.to_datetime(["2025-07-21", "2025-07-23", "2025-07-28"]),
    )

    result = harvest._weekly(series)

    assert result == {
        "dates": ["2025-07-23", "2025-07-28"],
        "values": [2.0, 3.0],
    }
    weekly_low = harvest.weekly_min(
        pd.Series(
            [3.0, 1.0, 2.0],
            index=pd.to_datetime(["2025-07-21", "2025-07-22", "2025-07-23"]),
        )
    )
    assert pd.DatetimeIndex(weekly_low.index).strftime("%Y-%m-%d").tolist() == ["2025-07-22"]


def test_fred_series_uses_official_api_and_drops_missing_values(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "observations": [
                    {"date": "2025-01-01", "value": "4.25"},
                    {"date": "2025-01-02", "value": "."},
                    {"date": "2025-01-03", "value": "4.50"},
                ]
            }

    def fake_get(url, **kwargs):
        captured.update({"url": url, **kwargs})
        return FakeResponse()

    monkeypatch.setenv("FRED_API_KEY", "test-key")
    monkeypatch.setattr(harvest.requests, "get", fake_get)

    result = harvest.fred_series("DGS10", start="2025-01-01")

    assert result.to_dict() == {
        pd.Timestamp("2025-01-01"): 4.25,
        pd.Timestamp("2025-01-03"): 4.5,
    }
    assert captured["url"] == harvest.FRED_OBSERVATIONS_URL
    assert captured["params"] == {
        "api_key": "test-key",
        "file_type": "json",
        "observation_start": "2025-01-01",
        "series_id": "DGS10",
        "sort_order": "asc",
    }


def test_cboe_daily_close_normalizes_columns_and_dates(monkeypatch) -> None:
    class FakeResponse:
        text = " date , close \n2025-01-03,18.25\n2025-01-02,19.50\n"

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(harvest.requests, "get", lambda *_args, **_kwargs: FakeResponse())

    result = harvest.cboe_daily_close("VIX")

    assert result.index.tolist() == [
        pd.Timestamp("2025-01-02"),
        pd.Timestamp("2025-01-03"),
    ]
    assert result.tolist() == [19.5, 18.25]


def test_shiller_month_code_is_not_treated_as_a_year_fraction() -> None:
    assert harvest.shiller_month_to_date(1871.01) == "1871-01-15"
    assert harvest.shiller_month_to_date(1871.1) == "1871-10-15"
    assert harvest.shiller_month_to_date(1871.12) == "1871-12-15"
    with pytest.raises(ValueError, match="invalid Shiller month code"):
        harvest.shiller_month_to_date(1871.13)


def test_shiller_payload_keeps_pre_cape_eps_history(monkeypatch) -> None:
    captured: dict[str, dict] = {}
    frame = pd.DataFrame(
        {
            "Date": [1871.01, 1881.01, 2023.09],
            "P": [4.44, 6.19, 4515.77],
            "D": [0.26, 0.27, None],
            "E": [0.40, 0.49, None],
            "CPI": [12.46, 10.16, 306.13],
            "Fraction": [1871.04, 1881.04, 2023.71],
            "Rate GS10": [5.32, 3.70, 4.09],
            "Price": [109.05, 170.0, 4515.77],
            "Dividend": [6.39, 7.4, None],
            "Price.1": [109.05, 170.0, 2_961_388.0],
            "Earnings": [9.82, 13.4, None],
            "Earnings.1": [9.82, 13.4, None],
            "CAPE": [None, 18.47, 30.81],
        }
    )
    response = SimpleNamespace(
        content=b"workbook",
        raise_for_status=lambda: None,
    )
    monkeypatch.setattr(harvest.requests, "get", lambda *_args, **_kwargs: response)
    monkeypatch.setattr(harvest.pd, "read_excel", lambda *_args, **_kwargs: frame)
    monkeypatch.setattr(
        harvest,
        "pin",
        lambda name, payload, **_kwargs: captured.update({name: payload}),
    )

    harvest.build_shiller_data()

    payload = captured["shiller_cape.json"]
    assert payload["dates"][0] == "1871-01-15"
    assert payload["cape"][0] is None
    assert payload["pe_ttm"][0] == 11.1
    assert payload["meta"]["latest_cape_date"] == "2023-09-15"


def test_parse_ofr_fsi_preserves_categories_and_latest_values() -> None:
    rows = []
    start = pd.Timestamp("2000-01-03")
    for index in range(5_001):
        date = start + pd.Timedelta(days=index)
        value = index / 1_000
        rows.append(
            f"{date.date()},{value},{value + 0.1},{value + 0.2},{value + 0.3},"
            f"{value + 0.4},{value + 0.5},{value + 0.6},{value + 0.7},{value + 0.8}"
        )
    header = (
        "Date,OFR FSI,Credit,Equity valuation,Safe assets,Funding,Volatility,"
        "United States,Other advanced economies,Emerging markets"
    )
    csv_text = "\n".join([header, *rows])
    last_date = start + pd.Timedelta(days=5_000)

    result = harvest._parse_ofr_fsi(
        csv_text,
        today=cast(pd.Timestamp, last_date + pd.Timedelta(days=2)),
    )

    assert result["meta"]["row_count"] == 5_001
    assert result["meta"]["coverage_end"] == str(last_date.date())
    assert result["latest"]["fsi"] == 5.0
    assert result["latest"]["credit"] == 5.1
    assert len(result["series"]["emerging_markets"]["values"]) == 5_001


def test_parse_ofr_fsi_rejects_duplicate_data() -> None:
    header = (
        "Date,OFR FSI,Credit,Equity valuation,Safe assets,Funding,Volatility,"
        "United States,Other advanced economies,Emerging markets"
    )
    row = "2026-07-01,1,1,1,1,1,1,1,1,1"
    duplicate_csv = "\n".join([header, *([row] * 5_001)])

    with pytest.raises(ValueError, match="duplicate dates"):
        harvest._parse_ofr_fsi(
            duplicate_csv,
            today=cast(pd.Timestamp, pd.Timestamp("2026-07-02")),
        )


def test_top_signal_requires_high_volume_bearish_day_near_ath() -> None:
    assert harvest.detect_top_signal(96.0, 97.0, 210.0, 100.0, 100.0)
    assert not harvest.detect_top_signal(94.0, 95.0, 210.0, 100.0, 100.0)
    assert not harvest.detect_top_signal(96.0, 97.0, 200.0, 100.0, 100.0)
    assert not harvest.detect_top_signal(97.0, 96.0, 210.0, 100.0, 100.0)


def test_forward_pe_uses_analyst_consensus_ntm_eps() -> None:
    assert harvest.calculate_forward_pe(6000.0, 300.0) == 20.0
    with pytest.raises(ValueError, match="NTM EPS must be positive"):
        harvest.calculate_forward_pe(6000.0, 0.0)


def test_merge_valuation_observation_replaces_same_date_and_sorts() -> None:
    existing = {
        "dates": ["2026-07-25", "2026-07-23"],
        "trailing_pe": [30.0, 29.0],
    }

    result = harvest.merge_valuation_observation(existing, "2026-07-25", 31.25)

    assert result == {
        "dates": ["2026-07-23", "2026-07-25"],
        "trailing_pe": [29.0, 31.25],
    }


def test_parse_sp500_changes_preserves_event_grain_and_cleans_citations() -> None:
    columns = pd.MultiIndex.from_tuples(
        [
            ("Effective Date", "Effective Date"),
            ("Added", "Ticker"),
            ("Added", "Security"),
            ("Removed", "Ticker"),
            ("Removed", "Security"),
            ("Reason", "Reason"),
        ]
    )
    table = pd.DataFrame(
        [
            ["July 1, 1976", "DIS", "Disney", "AYE", "Allegheny Energy", "Restructure[12]"],
            ["June 30, 2026", None, None, "CAG", "Conagra", "Market cap change.[5]"],
        ],
        columns=columns,
    )

    changes = harvest._parse_sp500_changes_table(table)

    assert changes == [
        {
            "effective_date": "2026-06-30",
            "addition": {"ticker": None, "name": None},
            "removal": {"ticker": "CAG", "name": "Conagra"},
            "reason": "Market cap change.",
        },
        {
            "effective_date": "1976-07-01",
            "addition": {"ticker": "DIS", "name": "Disney"},
            "removal": {"ticker": "AYE", "name": "Allegheny Energy"},
            "reason": "Restructure",
        },
    ]


def test_forward_eps_input_requires_source_and_current_asof(monkeypatch) -> None:
    monkeypatch.setenv("SP500_FORWARD_EPS_NTM", "300")
    monkeypatch.setenv("SP500_FORWARD_EPS_AS_OF", datetime.now(UTC).date().isoformat())
    monkeypatch.setenv("SP500_FORWARD_EPS_SOURCE", "licensed-provider")
    monkeypatch.setenv("SP500_FORWARD_EPS_LICENSE_SCOPE", "internal")

    result = harvest._forward_eps_input()

    assert result == {
        "ntm_eps": 300.0,
        "as_of": datetime.now(UTC).date().isoformat(),
        "source": "licensed-provider",
        "license_scope": "internal",
    }


def test_sec_identity_requires_project_name_and_monitored_email() -> None:
    assert (
        harvest.validate_sec_identity("  ArcOfMarket   research data@arcofmarket.com ")
        == "ArcOfMarket research data@arcofmarket.com"
    )
    with pytest.raises(ValueError, match="valid monitored email"):
        harvest.validate_sec_identity("ArcOfMarket research")
    with pytest.raises(ValueError, match="placeholder"):
        harvest.validate_sec_identity("ArcOfMarket research data@example.com")
    with pytest.raises(ValueError, match="project or company"):
        harvest.validate_sec_identity("data@arcofmarket.com")


def test_pin_stamps_dataset_sources_and_rights(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(harvest, "DATA", tmp_path)

    harvest.pin("source_catalog.json", {"value": 1})

    value = json.loads((tmp_path / "source_catalog.json").read_text(encoding="utf-8"))
    assert (tmp_path / "source_catalog.json").read_text(encoding="utf-8").endswith("\n")
    provenance = value["_provenance"]
    assert provenance["dataset_group"] == "source-transparency"
    assert provenance["source_ids"] == ["arc-methodology"]
    assert provenance["rights"]["access"] == {"public": True, "subscriber": True}


def test_cot_availability_uses_conservative_seven_day_lag() -> None:
    assert harvest.cot_availability_dates("2026-07-21") == {
        "report_date": "2026-07-21",
        "normal_release_date": "2026-07-24",
        "conservative_available_date": "2026-07-28",
    }


def test_cot_observations_preserve_first_seen_and_record_revisions() -> None:
    existing_row = {
        "date": "2026-07-21",
        "lev_long": 90,
        "first_observed_at": "2026-07-24T20:00:00Z",
        "row_sha256": "old-hash",
    }
    current_row = {
        "date": "2026-07-21",
        "lev_long": 100,
        "lev_short": 80,
        "lev_net": 20,
        "am_long": 50,
        "am_short": 60,
        "am_net": -10,
        "oi": 300,
        "lev_net_pct_oi": 6.67,
        "am_net_pct_oi": -3.33,
    }

    rows, revisions = harvest.attach_cot_observations(
        [current_row],
        {"series": [existing_row]},
        "2026-07-31T20:00:00Z",
    )

    assert rows[0]["strict_available_at"] == "2026-07-24T20:00:00Z"
    assert rows[0]["row_sha256"] != "old-hash"
    assert revisions == [
        {
            "report_date": "2026-07-21",
            "detected_at": "2026-07-31T20:00:00Z",
            "previous_hash": "old-hash",
            "new_hash": rows[0]["row_sha256"],
        }
    ]


def test_nber_period_preserves_month_resolution() -> None:
    assert harvest.nber_period("2020-02", "2020-04") == {
        "peak_month": "2020-02",
        "trough_month": "2020-04",
        "chart_start": "2020-02-01",
        "chart_end": "2020-04-30",
    }


def test_filing_metadata_uses_sec_acceptance_time() -> None:
    filing = SimpleNamespace(
        form="13F-HR/A",
        filing_date="2026-05-15",
        acceptance_datetime=datetime(2026, 5, 15, 17, 31, tzinfo=UTC),
        accession_no="000123-26-000001",
    )

    assert harvest.filing_metadata(filing) == {
        "form": "13F-HR/A",
        "filing_date": "2026-05-15",
        "accepted_at": "2026-05-15T17:31:00+00:00",
        "available_at": "2026-05-15T17:31:00+00:00",
        "accession_number": "000123-26-000001",
        "is_amendment": True,
        "point_in_time_safe": True,
    }


def test_weekly_sec_failures_block_only_when_identity_is_configured(monkeypatch) -> None:
    calls: list[tuple[str, bool]] = []

    def fake_run_section(label, _fn, *_args, blocking=True, **_kwargs) -> bool:
        calls.append((label, blocking))
        return True

    monkeypatch.setattr(harvest, "run_section", fake_run_section)
    monkeypatch.setattr(harvest, "_fetch_close", lambda _ticker: None)
    monkeypatch.delenv("SEC_IDENTITY", raising=False)
    harvest.run_weekly()
    assert ("内幕交易 Form4", False) in calls
    assert ("13F 机构持仓", False) in calls

    calls.clear()
    monkeypatch.setenv("SEC_IDENTITY", "ArcOfMarket data ops@arcofmarket.com")
    harvest.run_weekly()
    assert ("内幕交易 Form4", True) in calls
    assert ("13F 机构持仓", True) in calls


def test_mag7_equal_weight_normalizes_each_member_from_its_own_base(monkeypatch) -> None:
    captured: dict[str, dict] = {}
    index = pd.date_range("2024-01-01", periods=501, freq="B")
    growth = pd.Series(
        [1 + index_value / 5_000 for index_value in range(501)],
        index=index,
    )
    prices = {
        ticker: growth * (ticker_index + 1) * 10
        for ticker_index, ticker in enumerate(harvest.MAG7_TICKERS)
    }

    monkeypatch.setattr(harvest, "_fetch_close", lambda ticker: prices[ticker])
    monkeypatch.setattr(
        harvest,
        "pin",
        lambda name, payload, **_kwargs: captured.update({name: payload}),
    )

    harvest.build_mag7_data()

    values = captured["mag7_equal_weight.json"]["values"]
    assert values[0] == 100.0
    assert values[-1] == 110.0


def test_daily_distribution_keeps_extreme_tail_observations(monkeypatch) -> None:
    captured: dict[str, dict] = {}
    close = pd.Series(
        [100.0, 90.0, 100.8, 101.0],
        index=pd.date_range("2026-01-01", periods=4, freq="D"),
    )
    monkeypatch.setattr(
        harvest,
        "pin",
        lambda name, payload: captured.update({name: payload}),
    )

    harvest.build_daily_distribution("sp500", close)

    payload = captured["sp500_daily_dist.json"]
    assert sum(payload["counts"]) == payload["meta"]["n_days"] == 3
    assert payload["bins"][0] == "< -8.0%"
    assert payload["counts"][0] == 1
    assert payload["bins"][-1] == "≥ 8.0%"
    assert payload["counts"][-1] == 1


def test_period_return_uses_exact_number_of_sessions() -> None:
    close = pd.Series(
        [100.0, 101.0, 102.0, 103.0, 104.0, 110.0],
        index=pd.date_range("2026-01-01", periods=6, freq="B"),
    )

    assert harvest.period_return(close, 5) == 10.0
    assert harvest.period_return(close, 6) is None


def test_fetch_ndx_constituents_requires_complete_official_list(monkeypatch) -> None:
    rows = [
        {"symbol": f"T{index:03d}", "companyName": f"Company {index}"}
        for index in range(103)
    ]
    response = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"data": {"data": {"rows": rows}}},
    )
    monkeypatch.setattr(harvest.requests, "get", lambda *_args, **_kwargs: response)

    names = harvest.fetch_ndx_constituents()

    assert len(names) == 103
    assert names["T000"] == "Company 0"


def test_bulk_download_translates_class_share_symbols_for_yahoo(monkeypatch) -> None:
    captured: dict[str, list[str]] = {}
    index = pd.date_range("2026-01-01", periods=2, freq="B", tz="America/New_York")
    columns = pd.MultiIndex.from_product([["Close"], ["BF-B", "BRK-B"]])
    frame = pd.DataFrame([[10.0, 20.0], [11.0, 21.0]], index=index, columns=columns)

    def fake_download(tickers, **_kwargs):
        captured["tickers"] = tickers
        return frame

    monkeypatch.setattr(harvest.yf, "download", fake_download)

    result = harvest._download_close_matrix(["BF.B", "BRK.B"], period="5y")

    assert captured["tickers"] == ["BF-B", "BRK-B"]
    assert result.columns.tolist() == ["BF.B", "BRK.B"]
    assert result.index.tz is None


def test_monthly_heatmap_keeps_full_available_history(monkeypatch) -> None:
    captured: dict[str, dict] = {}
    close = pd.Series(
        range(100, 100 + 31 * 12),
        index=pd.date_range("1995-01-31", periods=31 * 12, freq="ME"),
        dtype=float,
    )
    monkeypatch.setattr(
        harvest,
        "pin",
        lambda name, payload: captured.update({name: payload}),
    )

    harvest.build_monthly_heatmap("sp500", close)

    payload = captured["sp500_monthly_heatmap.json"]
    assert len(payload["years"]) == 31
    assert payload["years"][0] == "1995"
    assert payload["years"][-1] == "2025"


def test_breadth_uses_per_date_eligible_denominator(monkeypatch) -> None:
    captured: dict[str, dict] = {}
    index = pd.date_range("2025-01-01", periods=260, freq="B")
    benchmark = pd.Series(range(100, 360), index=index, dtype=float)
    full_history = benchmark.copy()
    recent_history = benchmark.iloc[-100:].copy()

    close_matrix = pd.DataFrame(
        {
            "FULL-1": full_history,
            "FULL-2": full_history,
            "FULL-3": full_history,
            "FULL-4": full_history,
            "RECENT": recent_history,
        }
    )
    monkeypatch.setattr(
        harvest,
        "_download_close_matrix",
        lambda _tickers, **_kwargs: close_matrix,
    )
    monkeypatch.setattr(
        harvest,
        "pin",
        lambda name, payload: captured.update({name: payload}),
    )

    harvest.build_breadth(
        "sp500",
        benchmark,
        ["FULL-1", "FULL-2", "FULL-3", "FULL-4", "RECENT"],
    )

    payload = captured["sp500_breadth.json"]
    assert payload["latest_50ma"] == 100.0
    assert payload["latest_200ma"] == 100.0
    assert payload["pct_above_200ma"][0] == 100.0


def test_monthly_last_drops_current_incomplete_month() -> None:
    current = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    prior = current.to_period("M").start_time - pd.Timedelta(days=1)
    series = pd.Series([1.0, 2.0], index=[prior, current])

    result = harvest.monthly_last(series)

    assert result.index.tolist() == [prior]


def test_intrayear_return_uses_prior_year_end(monkeypatch) -> None:
    captured: dict[str, dict] = {}
    dates = pd.DatetimeIndex(
        [pd.Timestamp("2020-12-31"), *pd.date_range("2021-01-04", periods=65, freq="B")]
    )
    close = pd.Series([100.0, *[110.0 + index / 6.4 for index in range(65)]], index=dates)
    monkeypatch.setattr(harvest, "pin", lambda name, obj: captured.update({name: obj}))

    harvest.build_index_panels("test", close)

    row = captured["test_intrayear.json"]["rows"][0]
    assert row["ret"] == 20.0
    assert row["intra_dd"] == 0.0


def test_strict_update_reports_but_allows_optional_source_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        harvest,
        "run_daily",
        lambda: harvest._SOURCE_TRACE.update({"forward_pe": "missing"}),
    )
    monkeypatch.setattr(harvest, "pin", lambda *_args, **_kwargs: None)

    assert harvest.main(["--profile", "daily", "--strict"]) == 0
    assert harvest._FAILURES[0]["blocking"] is False


def test_strict_update_blocks_core_source_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        harvest,
        "run_daily",
        lambda: harvest._SOURCE_TRACE.update({"dgs10": "missing"}),
    )
    monkeypatch.setattr(harvest, "pin", lambda *_args, **_kwargs: None)

    assert harvest.main(["--profile", "daily", "--strict"]) == 1
    assert harvest._FAILURES[0]["blocking"] is True
