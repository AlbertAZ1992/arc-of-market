#!/usr/bin/env python3
"""ArcOfMarket · 数据哈希链。

每条记录锚定上一条链值、生成时间和当时全部数据文件的内容哈希。
验证会重算每条链值，并把最后一条记录与当前 data/ 文件逐一比对。
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HASH_CHAIN = DATA / "hash_chain.jsonl"
EXCLUDED_FILES = {"hash_chain.jsonl"}


def canonical_bytes(path: Path) -> bytes:
    """JSON 使用稳定序列化，其他文件使用原始字节。"""
    if path.suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return text.encode()
    return path.read_bytes()


def file_hash(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def snapshot(data_dir: Path = DATA) -> dict[str, str]:
    """记录全部 JSON/JSONL 数据文件，排除链文件自身。"""
    files = {}
    for path in sorted(data_dir.rglob("*.json*")):
        relative = path.relative_to(data_dir).as_posix()
        if relative in EXCLUDED_FILES or not path.is_file():
            continue
        files[relative] = file_hash(path)
    return files


def compute_chain(prev: str, timestamp: str, files: dict[str, str]) -> str:
    payload = json.dumps(
        {"prev": prev, "timestamp": timestamp, "files": files},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def load_records(chain_path: Path = HASH_CHAIN) -> list[dict]:
    if not chain_path.exists():
        return []
    records = []
    for number, line in enumerate(chain_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON at chain line {number}") from error
    return records


def verify(
    chain_path: Path = HASH_CHAIN,
    data_dir: Path = DATA,
    *,
    check_current: bool = True,
) -> bool:
    records = load_records(chain_path)
    if not records:
        print("  no chain to verify")
        return True

    prev = ""
    ok = True
    for index, record in enumerate(records, start=1):
        timestamp = record.get("timestamp", "")
        files = record.get("files", {})
        expected = compute_chain(prev, timestamp, files)
        if record.get("prev") != prev or record.get("chain") != expected:
            print(f"  ✗ chain break at line {index}")
            ok = False
        prev = record.get("chain", "")

    if check_current and records[-1].get("files") != snapshot(data_dir):
        print("  ✗ current data does not match the latest chain record")
        ok = False

    print(f"  chain {'OK' if ok else 'BROKEN'} ({len(records)} entries)")
    return ok


def append_day(
    chain_path: Path = HASH_CHAIN,
    data_dir: Path = DATA,
) -> None:
    data_dir.mkdir(exist_ok=True)
    if chain_path.exists() and not verify(chain_path, data_dir, check_current=False):
        raise RuntimeError("refusing to append to a broken chain")

    records = load_records(chain_path)
    prev = records[-1]["chain"] if records else ""
    files = snapshot(data_dir)
    if not files:
        raise RuntimeError("no data files to anchor")

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    chain = compute_chain(prev, timestamp, files)
    record = {
        "date": timestamp[:10],
        "timestamp": timestamp,
        "files": files,
        "prev": prev,
        "chain": chain,
    }
    with chain_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"  anchored chain={chain[:16]}… ({len(files)} files)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        raise SystemExit(0 if verify() else 1)
    append_day()
