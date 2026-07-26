#!/usr/bin/env python3
"""ArcOfMarket · 数据变更审计。

记录本次管线相对 Git HEAD 的 data/ 变更，并在出现删除时让自动化失败。
审计报告只描述当前工作区，不声称能够独立证明历史数据从未被改写。
"""

import json
import math
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.dataset_rights import validate_registry

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATASET_REGISTRY = ROOT / "config" / "dataset-registry.json"
IGNORED_REPORTS = {"data/audit_report.json", "data/hash_chain.jsonl"}
DATE_ARRAY_EXCLUSIONS = {"equity_curve", "episodes", "periods", "rows"}

DAILY_REQUIRED = {
    "breadth_pulse.json",
    "financial_stress.json",
    "macro_rates.json",
    "ndx_valuation_proxy.json",
    "regime_rotation.json",
    "rs_leaders.json",
    "source_catalog.json",
    "sp500_total_return.json",
    "vol_family.json",
} | {
    f"{prefix}_{panel}.json"
    for prefix in ("sp500", "ixic", "ndx")
    for panel in (
        "annual",
        "bullbear",
        "century",
        "distribution",
        "drawdowns",
        "extremes",
        "holding",
        "intrayear",
        "rolling5y",
        "rollmatrix",
        "seasonality",
        "volatility",
    )
}

WEEKLY_REQUIRED = {
    "cot_vix.json",
    "equity_allocation.json",
    "macro_growth.json",
    "macro_prices.json",
    "recessions.json",
    "source_catalog.json",
    "sp500_changes.json",
    "sp500_constituents.json",
}

COVERAGE_RULES = {
    "equity_allocation.json": ("dates", 250, 500),
    "financial_stress.json": ("series.fsi.dates", 5_000, 10),
    "ixic_century.json": ("dates", 10_000, 10),
    "macro_growth.json": ("unrate.dates", 250, 100),
    "macro_prices.json": ("cpi_yoy.dates", 200, 100),
    "macro_rates.json": ("dgs10.dates", 1_000, 14),
    "ndx_century.json": ("dates", 9_000, 10),
    "ndx_valuation_proxy.json": ("dates", 1, 10),
    "regime_rotation.json": ("dates", 3_000, 10),
    "sp500_century.json": ("dates", 20_000, 10),
    "sp500_total_return.json": ("dates", 9_000, 10),
}


def validate_sp500_changes(obj: Any) -> list[dict[str, str]]:
    if not isinstance(obj, dict):
        return [{"severity": "blocking", "path": "sp500_changes.json", "issue": "not an object"}]
    changes = obj.get("changes")
    if not isinstance(changes, list) or len(changes) < 300:
        count = len(changes) if isinstance(changes, list) else 0
        return [
            {
                "severity": "blocking",
                "path": "sp500_changes.json",
                "issue": f"coverage {count} rows below minimum 300",
            }
        ]
    keys = [
        (
            row.get("effective_date"),
            (row.get("addition") or {}).get("ticker"),
            (row.get("removal") or {}).get("ticker"),
        )
        for row in changes
        if isinstance(row, dict)
    ]
    issues = []
    if len(keys) != len(changes) or len(set(keys)) != len(keys):
        issues.append(
            {
                "severity": "blocking",
                "path": "sp500_changes.json",
                "issue": "invalid or duplicate event grain",
            }
        )
    if keys != sorted(keys, key=lambda key: str(key[0]), reverse=True):
        issues.append(
            {
                "severity": "blocking",
                "path": "sp500_changes.json",
                "issue": "events are not sorted by effective date descending",
            }
        )
    revision = ((obj.get("meta") or {}).get("source") or {}).get("revision")
    if not isinstance(revision, dict) or not revision.get("id") or not revision.get("url"):
        issues.append(
            {
                "severity": "blocking",
                "path": "sp500_changes.json",
                "issue": "source revision provenance missing",
            }
        )
    return issues


def git_status_entries(root: Path = ROOT) -> list[dict[str, str]]:
    """返回 data/ 的 tracked 与 untracked 变更。"""
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", "data/"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    entries = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:].split(" -> ")[-1]
        if path in IGNORED_REPORTS:
            continue
        entries.append({"status": status, "path": path})
    return entries


def registered_data_paths(registry_path: Path = DATASET_REGISTRY) -> set[str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    groups = registry.get("groups", [])
    return {
        f"data/{filename}"
        for group in groups
        if isinstance(group, dict)
        for filename in group.get("files", [])
        if isinstance(filename, str)
    }


def nested_value(obj: Any, dotted_path: str) -> Any:
    current = obj
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid constant {value}")


def validate_date_arrays(
    obj: Any,
    source: str,
    location: str = "",
) -> list[dict[str, str]]:
    issues = []
    if isinstance(obj, dict):
        date_values = obj.get("dates")
        if isinstance(date_values, list):
            date_location = location.rstrip(".") or "root"
            if date_values != sorted(date_values):
                issues.append(
                    {
                        "severity": "blocking",
                        "path": source,
                        "issue": f"{date_location} dates unsorted",
                    }
                )
            if len(date_values) != len(set(date_values)):
                issues.append(
                    {
                        "severity": "blocking",
                        "path": source,
                        "issue": f"{date_location} dates contain duplicates",
                    }
                )
            for key, values in obj.items():
                if (
                    key not in DATE_ARRAY_EXCLUSIONS
                    and key != "dates"
                    and isinstance(values, list)
                    and values
                    and not isinstance(values[0], dict)
                    and len(values) != len(date_values)
                ):
                    issues.append(
                        {
                            "severity": "blocking",
                            "path": source,
                            "issue": (
                                f"{date_location}.{key} length {len(values)} != "
                                f"dates length {len(date_values)}"
                            ),
                        }
                    )
        for key, value in obj.items():
            child_location = f"{location}{key}."
            issues.extend(validate_date_arrays(value, source, child_location))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            issues.extend(validate_date_arrays(value, source, f"{location}{index}."))
    elif isinstance(obj, float) and not math.isfinite(obj):
        issues.append(
            {"severity": "blocking", "path": source, "issue": f"{location} is not finite"}
        )
    return issues


def validate_data(
    data_dir: Path = DATA,
    *,
    validate_rights: bool = True,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    objects: dict[str, Any] = {}
    for path in sorted(data_dir.glob("*.json")):
        try:
            objects[path.name] = json.loads(
                path.read_text(encoding="utf-8"),
                parse_constant=reject_json_constant,
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            issues.append(
                {"severity": "blocking", "path": path.name, "issue": f"invalid JSON: {error}"}
            )
            continue
        issues.extend(validate_date_arrays(objects[path.name], path.name))
    if "sp500_changes.json" in objects:
        issues.extend(validate_sp500_changes(objects["sp500_changes.json"]))

    meta = objects.get("meta.json", {})
    profile = meta.get("profile") if isinstance(meta, dict) else None
    required = set()
    if profile in ("daily", "full"):
        required.update(DAILY_REQUIRED)
    if profile in ("weekly", "full"):
        required.update(WEEKLY_REQUIRED)
    for filename in sorted(required):
        if filename not in objects:
            issues.append(
                {"severity": "blocking", "path": filename, "issue": "required file missing"}
            )
            continue
        provenance = objects[filename].get("_provenance")
        if not isinstance(provenance, dict) or not provenance.get("generated_at"):
            issues.append(
                {
                    "severity": "blocking",
                    "path": filename,
                    "issue": "required provenance.generated_at missing",
                }
            )

    now = datetime.now(UTC).date()
    for filename, (date_path, minimum_rows, maximum_age_days) in COVERAGE_RULES.items():
        if filename not in objects:
            continue
        values = nested_value(objects[filename], date_path)
        if not isinstance(values, list) or len(values) < minimum_rows:
            actual = len(values) if isinstance(values, list) else 0
            issues.append(
                {
                    "severity": "blocking",
                    "path": filename,
                    "issue": f"coverage {actual} rows below minimum {minimum_rows}",
                }
            )
            continue
        try:
            latest = datetime.fromisoformat(str(values[-1])).date()
        except ValueError:
            issues.append(
                {"severity": "blocking", "path": filename, "issue": "latest date is invalid"}
            )
            continue
        age_days = (now - latest).days
        if age_days > maximum_age_days:
            issues.append(
                {
                    "severity": "blocking",
                    "path": filename,
                    "issue": f"latest observation is {age_days} days old",
                }
            )

    if isinstance(meta, dict):
        failure_groups = [meta.get("failures", [])]
        profile_runs = meta.get("profile_runs", {})
        if isinstance(profile_runs, dict):
            failure_groups.extend(
                run.get("failures", []) for run in profile_runs.values() if isinstance(run, dict)
            )
        seen_failures: set[tuple[str, str, bool]] = set()
        for failure in (
            item for group in failure_groups if isinstance(group, list) for item in group
        ):
            if not isinstance(failure, dict):
                continue
            failure_key = (
                str(failure.get("section")),
                str(failure.get("error")),
                bool(failure.get("blocking", True)),
            )
            if failure_key in seen_failures:
                continue
            seen_failures.add(failure_key)
            issues.append(
                {
                    "severity": "blocking" if failure.get("blocking", True) else "warning",
                    "path": "meta.json",
                    "issue": f"{failure.get('section')}: {failure.get('error')}",
                }
            )
    if validate_rights:
        for registry_issue in validate_registry(data_dir=data_dir):
            issues.append(
                {
                    "severity": "blocking",
                    "path": "config/dataset-registry.json",
                    "issue": registry_issue,
                }
            )
    return issues


def main() -> int:
    DATA.mkdir(exist_ok=True)
    entries = git_status_entries()
    deleted = [entry["path"] for entry in entries if "D" in entry["status"]]
    registered_paths = registered_data_paths()
    unapproved_deleted = [path for path in deleted if path in registered_paths]
    quality_issues = validate_data()
    blocking_issues = [issue for issue in quality_issues if issue["severity"] == "blocking"]
    audit = {
        "updated": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "changes": entries,
        "changed_files": [entry["path"] for entry in entries],
        "delta": len(entries),
        "reliable": not unapproved_deleted and not blocking_issues,
        "deleted_files": deleted,
        "retired_files": [path for path in deleted if path not in registered_paths],
        "quality_issues": quality_issues,
        "note": (
            "本报告记录当前工作区相对 Git HEAD 的数据变更，并检查必需文件、覆盖、"
            "新鲜度、日期及数组一致性；哈希链负责检测已发布链记录的删改。"
        ),
    }
    report = DATA / "audit_report.json"
    report.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"  audit: {len(entries)} changed files, {len(deleted)} deleted, "
        f"{len(blocking_issues)} blocking quality issues"
    )
    return 1 if unapproved_deleted or blocking_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
