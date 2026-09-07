#!/usr/bin/env python3
"""Fetch and publish one compact ArcOfMarket Market Release."""

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Standalone CLI exposes the repository's src-layout before application imports.
# ruff: noqa: E402
ROOT = Path(__file__).resolve().parent.parent
for import_root in (ROOT, ROOT / "src"):
    import_path = str(import_root)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

from arc_market.collection import FetcherDependencies, MarketCollector
from arc_market.config import MarketConfig, load_market_config
from arc_market.errors import MarketDataError
from arc_market.fetchers.cboe import CboeVixFetcher
from arc_market.fetchers.cftc import CftcFetcher
from arc_market.fetchers.fred import FredFetcher
from arc_market.fetchers.ofr import OfrFetcher
from arc_market.fetchers.treasury import TreasuryFetcher
from arc_market.fetchers.wikipedia import WikipediaUniverseFetcher
from arc_market.fetchers.yahoo import YahooPriceFetcher
from arc_market.pipeline import build_release_core
from arc_market.release import MarketReleasePublisher, MarketReleaseReceipt

NEW_YORK = ZoneInfo("America/New_York")


def last_completed_market_date(now: datetime | None = None) -> date:
    current = now.astimezone(NEW_YORK) if now is not None else datetime.now(NEW_YORK)
    candidate = current.date()
    if current.weekday() >= 5 or current.timetz().replace(tzinfo=None) < time(20):
        candidate -= timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def producer_commit(root: Path) -> str:
    from_environment = os.environ.get("GITHUB_SHA", "").strip()
    if from_environment:
        return from_environment
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_live_collector(root: Path, *, strict: bool) -> tuple[MarketConfig, MarketCollector]:
    config = load_market_config(root / "config" / "market-data-v2.json")
    dependencies = FetcherDependencies(
        yahoo=YahooPriceFetcher(),
        wikipedia=WikipediaUniverseFetcher(),
        fred=FredFetcher(),
        cboe=CboeVixFetcher(),
        ofr=OfrFetcher(),
        treasury=TreasuryFetcher(),
        cftc=CftcFetcher(),
    )
    return config, MarketCollector(config, dependencies, strict=strict)


def run_market_data(
    root: Path,
    *,
    target_date: date,
    strict: bool,
    generated_at: datetime | None = None,
) -> MarketReleaseReceipt:
    config, collector = build_live_collector(root, strict=strict)
    collected = collector.collect(target_date)
    core = build_release_core(
        config,
        collected,
        producer_commit=producer_commit(root),
    )
    return MarketReleasePublisher(root / "releases").publish(
        core,
        generated_at=generated_at or datetime.now(UTC),
    )


def write_github_output(
    path: Path,
    release_id: str,
    release_path: Path,
    latest_path: Path,
) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"market_release_id={release_id}\n")
        handle.write(f"market_release={release_path}\n")
        handle.write(f"market_latest={latest_path}\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish ArcOfMarket Market Data v2")
    parser.add_argument("--as-of", type=date.fromisoformat)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--github-output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        receipt = run_market_data(
            ROOT,
            target_date=args.as_of or last_completed_market_date(),
            strict=args.strict,
        )
    except (MarketDataError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"market release stopped: {error}")
        return 1
    if args.github_output is not None:
        write_github_output(
            args.github_output,
            receipt.release_id,
            receipt.path,
            receipt.latest_path,
        )
    print(f"market release published: {receipt.release_id}")
    print(f"latest: {receipt.latest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
