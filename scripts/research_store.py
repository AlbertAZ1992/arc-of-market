#!/usr/bin/env python3
"""Initialize and append Market Releases to the local research store."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

# Standalone CLI exposes the repository's src-layout before application imports.
# ruff: noqa: E402
ROOT = Path(__file__).resolve().parent.parent
for import_root in (ROOT, ROOT / "src"):
    import_path = str(import_root)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

from arc_market.research_store import ResearchStore


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage the point-in-time Research Store")
    parser.add_argument("--database", type=Path, default=ROOT / ".research-store/research.db")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")
    subparsers.add_parser("status")
    ingest = subparsers.add_parser("ingest-latest")
    ingest.add_argument("--release", type=Path, default=ROOT / "releases/market/latest.json")
    return parser.parse_args(argv)


def _read_release(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Market Release envelope must be an object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    store = ResearchStore(args.database)
    try:
        if args.command == "ingest-latest":
            inserted = store.ingest(_read_release(args.release))
            print(
                "research observation appended"
                if inserted
                else "research observation already present"
            )
        print(json.dumps(store.status(), ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"research store stopped: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
