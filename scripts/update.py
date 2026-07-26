#!/usr/bin/env python3
"""运行采集、审计和哈希链的统一入口。"""

import argparse
from collections.abc import Sequence
from pathlib import Path

from scripts import audit, chain, harvest


def snapshot_data(data_dir: Path) -> dict[Path, bytes]:
    """保存更新前的数据文件，用于严格失败时回滚半成品。"""
    if not data_dir.exists():
        return {}
    return {
        path.relative_to(data_dir): path.read_bytes()
        for path in data_dir.rglob("*")
        if path.is_file()
    }


def restore_data(data_dir: Path, snapshot: dict[Path, bytes]) -> None:
    """把 data/ 恢复到更新前的逐文件状态。"""
    data_dir.mkdir(parents=True, exist_ok=True)
    for path in data_dir.rglob("*"):
        if path.is_file() and path.relative_to(data_dir) not in snapshot:
            path.unlink()
    for relative_path, content in snapshot.items():
        path = data_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="更新并锚定 ArcOfMarket 数据")
    parser.add_argument(
        "--profile",
        choices=("daily", "weekly", "full"),
        default="daily",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="仅用于诊断：允许数据源失败后仍生成审计和链记录",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    harvest_args = ["--profile", args.profile]
    if not args.allow_partial:
        harvest_args.append("--strict")

    data_snapshot = snapshot_data(harvest.DATA)
    try:
        result = harvest.main(harvest_args)
    except Exception:
        restore_data(harvest.DATA, data_snapshot)
        raise
    if result:
        restore_data(harvest.DATA, data_snapshot)
        print("update stopped: data source failures were recorded in data/meta.json")
        print("data/ restored to its pre-update state")
        return result
    if audit.main():
        restore_data(harvest.DATA, data_snapshot)
        print("update stopped: data deletions require manual review")
        print("data/ restored to its pre-update state")
        return 1

    chain.append_day()
    if not chain.verify():
        restore_data(harvest.DATA, data_snapshot)
        print("update stopped: hash chain verification failed")
        print("data/ restored to its pre-update state")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
