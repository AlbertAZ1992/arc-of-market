#!/usr/bin/env bash

set -euo pipefail

DRY_RUN=0
FORCE=0
while [[ "${1:-}" == --* ]]; do
	case "$1" in
	--dry-run) DRY_RUN=1 ;;
	--force) FORCE=1 ;;
	*)
		echo "error: unknown option: $1" >&2
		exit 1
		;;
	esac
	shift
done

INPUT="${1:-PROJECT_SOURCES.md}"
TARGET_DIR="${2:-}"

if [[ -z "$TARGET_DIR" ]]; then
	echo "error: target directory is required" >&2
	exit 1
fi

python3 - "$INPUT" "$TARGET_DIR" "$DRY_RUN" "$FORCE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    input_path = Path(sys.argv[1]).expanduser()
    target_dir = Path(sys.argv[2]).expanduser()
    dry_run = sys.argv[3] == "1"
    force = sys.argv[4] == "1"
    lines = input_path.read_text(encoding="utf-8").splitlines(keepends=True)
    sections = list(iter_sections(lines))
    expected = expected_file_count(lines)
    if expected != len(sections):
        raise ValueError(f"expected {expected} files but found {len(sections)} sections")
    if not dry_run:
        assert_safe_target(target_dir, force)

    for rel_path, content in sections:
        destination = safe_destination(target_dir, rel_path)
        if dry_run:
            print(f"would write {destination}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    action = "would write" if dry_run else "wrote"
    print(f"{action} {len(sections)} files from {input_path} into {target_dir}")
    return 0


def expected_file_count(lines: list[str]) -> int:
    for line in lines:
        if line.startswith("Total files: "):
            return int(line.removeprefix("Total files: ").strip())
    raise ValueError("source export is missing its file count")


def assert_safe_target(target_dir: Path, force: bool) -> None:
    if target_dir.exists() and any(target_dir.iterdir()) and not force:
        raise ValueError(
            f"target directory is not empty: {target_dir}; use --force to allow overwrites"
        )


def iter_sections(lines: list[str]):
    index = 0
    while index < len(lines):
        if not is_section_start(lines, index):
            index += 1
            continue

        rel_path = lines[index + 2].strip()[4:-1]
        index += 4
        opening = lines[index].rstrip("\n")
        fence = opening_fence(opening)
        if len(fence) < 3:
            raise ValueError(f"source section has no code fence: {rel_path}")

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
        index + 4 < len(lines)
        and lines[index] == "---\n"
        and lines[index + 1] == "\n"
        and lines[index + 2].startswith("## `")
        and lines[index + 2].rstrip("\n").endswith("`")
        and lines[index + 3] == "\n"
    )


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
