#!/usr/bin/env python3
"""Fail closed unless tracked release and dataset-rights reviews are complete."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from scripts.dataset_rights import validate_registry

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "config" / "data-license-review.json"


def validate_review(path: Path = REVIEW, scope: str = "public") -> list[str]:
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"license review file is unreadable: {error}"]

    issues = []
    if review.get("schema_version") != 1:
        issues.append("unsupported license review schema")
    approval_field = f"{scope}_release_approved"
    if review.get(approval_field) is not True:
        issues.append(f"{scope} release is not approved")
    blockers = review.get("blockers")
    if not isinstance(blockers, list):
        issues.append("blockers must be a list")
    elif blockers:
        issues.extend(f"blocker: {blocker}" for blocker in blockers)
    for field in ("reviewed_at", "reviewed_by", "approval_reference"):
        if not review.get(field):
            issues.append(f"{field} is required")
    return issues


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate release data rights")
    parser.add_argument("--scope", choices=("public", "subscriber"), default="public")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    issues = [*validate_review(scope=args.scope), *validate_registry()]
    if issues:
        print(f"{args.scope} publication blocked:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"{args.scope} publication license gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
