#!/usr/bin/env bash
#
# apply_sources.sh — 从 scripts/export_sources.sh 生成的 Markdown 还原源码文件。
#
# 用法:
#   ./scripts/apply_sources.sh                         # 读取 PROJECT_SOURCES.md，写回当前项目
#   ./scripts/apply_sources.sh PROJECT_SOURCES.md out  # 写入 out 目录
#   ./scripts/apply_sources.sh --dry-run PROJECT_SOURCES.md out
#
# 行为：
# - 创建或覆盖 Markdown 中列出的文本文件。
# - 不删除 Markdown 中不存在的文件。
# - 跳过导出时标记为 binary/non-text omitted 的文件。
# - 拒绝绝对路径和包含 .. 的路径，避免写出目标目录。

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
	DRY_RUN=1
	shift
fi

INPUT="${1:-PROJECT_SOURCES.md}"
TARGET_DIR="${2:-$PROJECT_ROOT}"

python3 - "$INPUT" "$TARGET_DIR" "$DRY_RUN" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    input_path = Path(sys.argv[1]).expanduser()
    target_dir = Path(sys.argv[2]).expanduser()
    dry_run = sys.argv[3] == "1"

    lines = input_path.read_text(encoding="utf-8").splitlines(keepends=True)
    written = 0
    skipped = 0

    for rel_path, content in iter_sections(lines):
        destination = safe_destination(target_dir, rel_path)
        if content is None:
            skipped += 1
            print(f"skip non-text section: {rel_path}", file=sys.stderr)
            continue
        if dry_run:
            print(f"would write {destination}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
        written += 1

    action = "would write" if dry_run else "wrote"
    print(f"{action} {written} files from {input_path} into {target_dir}")
    if skipped:
        print(f"skipped {skipped} non-text sections")
    return 0


def iter_sections(lines: list[str]):
    index = 0
    while index < len(lines):
        if not is_section_start(lines, index):
            index += 1
            continue

        rel_path = lines[index + 2].strip()[4:-1]
        index += 4
        if index >= len(lines):
            yield rel_path, None
            break

        opening = lines[index].rstrip("\n")
        fence = opening_fence(opening)
        if not fence.startswith("```"):
            index = skip_to_next_section(lines, index)
            yield rel_path, None
            continue

        index += 1
        content: list[str] = []
        while index < len(lines) and lines[index].rstrip("\n") != fence:
            content.append(lines[index])
            index += 1
        if index >= len(lines):
            raise ValueError(f"source section is missing its closing fence: {rel_path}")
        index += 1
        yield rel_path, "".join(content)


def is_section_start(lines: list[str], index: int) -> bool:
    return (
        index + 3 < len(lines)
        and lines[index] == "---\n"
        and lines[index + 1] == "\n"
        and lines[index + 2].startswith("## `")
        and lines[index + 2].rstrip("\n").endswith("`")
        and lines[index + 3] == "\n"
    )


def skip_to_next_section(lines: list[str], index: int) -> int:
    index += 1
    while index < len(lines) and not is_section_start(lines, index):
        index += 1
    return index


def opening_fence(line: str) -> str:
    size = 0
    while size < len(line) and line[size] == "`":
        size += 1
    return line[:size]


def safe_destination(target_dir: Path, rel_path: str) -> Path:
    path = Path(rel_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe path in source export: {rel_path}")
    return target_dir / path


if __name__ == "__main__":
    raise SystemExit(main())
PY
