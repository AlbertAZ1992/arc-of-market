#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORT_DIR="${1:-$PROJECT_ROOT/project-export}"
TEMP_DIR="$(mktemp -d)"

cleanup() {
	trash "$TEMP_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if ! command -v shasum >/dev/null 2>&1; then
	echo "error: this script requires shasum" >&2
	exit 1
fi

mkdir -p "$TEMP_DIR/package"
bash "$PROJECT_ROOT/scripts/export_sources.sh" "$PROJECT_ROOT/PROJECT_SOURCES.md"
cp "$PROJECT_ROOT/PROJECT_SOURCES.md" "$TEMP_DIR/package/PROJECT_SOURCES.md"
cp "$PROJECT_ROOT/scripts/apply_sources.sh" "$TEMP_DIR/package/restore_project.sh"
cp "$PROJECT_ROOT/scripts/project-export-readme.md" "$TEMP_DIR/package/README.md"
chmod +x "$TEMP_DIR/package/restore_project.sh"

RESTORE_DIR="$TEMP_DIR/restored"
bash "$TEMP_DIR/package/restore_project.sh" \
	"$TEMP_DIR/package/PROJECT_SOURCES.md" "$RESTORE_DIR"
bash "$RESTORE_DIR/scripts/export_sources.sh" "$TEMP_DIR/reexported.md"
cmp "$TEMP_DIR/package/PROJECT_SOURCES.md" "$TEMP_DIR/reexported.md"

(
	cd "$TEMP_DIR/package"
	shasum -a 256 PROJECT_SOURCES.md restore_project.sh README.md >SHA256SUMS
)

mkdir -p "$EXPORT_DIR"
cp "$TEMP_DIR/package/PROJECT_SOURCES.md" "$EXPORT_DIR/PROJECT_SOURCES.md"
cp "$TEMP_DIR/package/restore_project.sh" "$EXPORT_DIR/restore_project.sh"
cp "$TEMP_DIR/package/README.md" "$EXPORT_DIR/README.md"
cp "$TEMP_DIR/package/SHA256SUMS" "$EXPORT_DIR/SHA256SUMS"

echo "wrote verified data project export to $EXPORT_DIR"
