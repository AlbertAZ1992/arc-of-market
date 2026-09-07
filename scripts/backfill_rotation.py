#!/usr/bin/env python3
"""Build reconstructed public observations; never publish releases or send emails."""

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

# Standalone CLI exposes the repository's src-layout before application imports.
# ruff: noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arc_market.fetchers.yahoo import YahooPriceFetcher
from arc_market.rotation_history import build_rotation_history


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.start > args.end or args.end >= datetime.now(UTC).date():
        parser.error("Use an ordered historical date range ending before today")
    prices = YahooPriceFetcher().fetch(("QQQ", "VTV"), args.end)
    result = build_rotation_history(
        prices, start=args.start, end=args.end, computed_at=datetime.now(UTC)
    )
    entries = result["entries"]
    if not isinstance(entries, list):
        raise TypeError("Rotation history entries are invalid")
    payload = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote {len(entries)} reconstructed sessions to {args.output}")
        return
    print(payload, end="")


if __name__ == "__main__":
    main()
