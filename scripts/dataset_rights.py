#!/usr/bin/env python3
"""Validate per-dataset source lineage and publication rights."""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATASET_REGISTRY = ROOT / "config" / "dataset-registry.json"
SOURCE_REGISTRY = ROOT / "config" / "source-registry.json"
POLICIES = {
    "public": ROOT / "config" / "public-data-policy.json",
    "subscriber": ROOT / "config" / "subscriber-data-policy.json",
}
APPROVED_SOURCE_STATUSES = {
    "approved",
    "approved-with-attribution",
    "approved-with-fair-access",
    "citation-required",
}
APPROVED_DERIVED_OUTPUTS = {"allowed", "allowed-with-attribution"}
PUBLIC_CHART_DECISION_STATUSES = {
    "approved-for-public-chart-display",
    "approved-for-public-research-display",
}


def load_object(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return {}, [f"{path.name} is unreadable: {error}"]
    if not isinstance(value, dict):
        return {}, [f"{path.name} must contain a JSON object"]
    return value, []


def expand_groups(registry: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    datasets: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    groups = registry.get("groups")
    if not isinstance(groups, list):
        return datasets, ["dataset registry groups must be a list"]
    for group in groups:
        if not isinstance(group, dict) or not group.get("id"):
            issues.append("each dataset group must be an object with an id")
            continue
        files = group.get("files")
        if not isinstance(files, list) or not files:
            issues.append(f"group {group['id']} must list at least one file")
            continue
        for filename in files:
            if not isinstance(filename, str) or not filename.endswith(".json"):
                issues.append(f"group {group['id']} has an invalid filename")
            elif filename in datasets:
                issues.append(f"{filename} appears in more than one dataset group")
            else:
                datasets[filename] = group
    return datasets, issues


def validate_group(
    group: dict[str, Any],
    source_statuses: dict[str, str],
) -> list[str]:
    group_id = str(group.get("id"))
    issues: list[str] = []
    source_ids = group.get("source_ids")
    access = group.get("access")
    if not isinstance(source_ids, list) or not source_ids:
        issues.append(f"group {group_id} must list source_ids")
        return issues
    if not isinstance(access, dict):
        issues.append(f"group {group_id} must define access")
        return issues
    for scope in POLICIES:
        if not isinstance(access.get(scope), bool):
            issues.append(f"group {group_id} access.{scope} must be boolean")
    for source_id in source_ids:
        if source_id not in source_statuses:
            issues.append(f"group {group_id} references unknown source {source_id}")
    approval_reference = str(group.get("approval_reference", ""))
    has_public_chart_decision = (
        group.get("status") in PUBLIC_CHART_DECISION_STATUSES
        and approval_reference.startswith("Product owner data-display decision ")
    )
    if access.get("public") or access.get("subscriber"):
        if group.get("derived_output") not in APPROVED_DERIVED_OUTPUTS:
            issues.append(f"group {group_id} exposes a scope without approved derived output")
        if not group.get("approval_reference"):
            issues.append(f"group {group_id} exposes a scope without approval_reference")
    if access.get("public") and not has_public_chart_decision:
        for source_id in source_ids:
            if source_statuses.get(source_id) not in APPROVED_SOURCE_STATUSES:
                issues.append(f"group {group_id} uses non-public source {source_id}")
    return issues


def validate_policy(
    scope: str,
    policy: dict[str, Any],
    datasets: dict[str, dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if policy.get("schema_version") != 1 or policy.get("default") != "deny":
        issues.append(f"{scope} policy must use schema 1 with default deny")
    files = policy.get("files")
    if not isinstance(files, dict):
        return [*issues, f"{scope} policy files must be an object"]
    allowed = {name for name, rule in files.items() if rule.get(scope) is True}
    registered = {name for name, group in datasets.items() if group["access"].get(scope)}
    for filename in sorted(allowed - registered):
        issues.append(f"{scope} policy allows unapproved dataset {filename}")
    for filename in sorted(registered - allowed):
        issues.append(f"dataset registry allows {scope} but policy omits {filename}")
    return issues


def dataset_record(
    filename: str,
    registry_path: Path = DATASET_REGISTRY,
) -> dict[str, Any]:
    registry, issues = load_object(registry_path)
    datasets, group_issues = expand_groups(registry)
    issues.extend(group_issues)
    if issues:
        raise ValueError("; ".join(issues))
    if filename not in datasets:
        raise ValueError(f"unregistered data file {filename}")
    group = datasets[filename]
    return {
        "group": group["id"],
        "source_ids": group["source_ids"],
        "access": group["access"],
        "derived_output": group["derived_output"],
        "status": group["status"],
    }


def validate_registry(
    data_dir: Path = DATA,
    registry_path: Path = DATASET_REGISTRY,
    source_path: Path = SOURCE_REGISTRY,
    policies: dict[str, Path] = POLICIES,
) -> list[str]:
    registry, issues = load_object(registry_path)
    source_registry, source_issues = load_object(source_path)
    issues.extend(source_issues)
    if registry.get("schema_version") != 1 or registry.get("default_access") != "deny":
        issues.append("dataset registry must use schema 1 with default deny")
    datasets, group_issues = expand_groups(registry)
    issues.extend(group_issues)
    source_rows = source_registry.get("sources", [])
    source_statuses = {
        row["id"]: row["public_status"]
        for row in source_rows
        if isinstance(row, dict) and row.get("id") and row.get("public_status")
    }
    seen_groups: set[str] = set()
    for group in datasets.values():
        group_id = str(group["id"])
        if group_id not in seen_groups:
            issues.extend(validate_group(group, source_statuses))
            seen_groups.add(group_id)
    actual_files = {path.name for path in data_dir.glob("*.json")}
    for filename in sorted(actual_files - datasets.keys()):
        issues.append(f"unregistered data file {filename}")
    for filename in sorted(datasets.keys() - actual_files):
        if not datasets[filename].get("optional"):
            issues.append(f"registered data file is missing: {filename}")
    for scope, policy_path in policies.items():
        policy, policy_issues = load_object(policy_path)
        issues.extend(policy_issues)
        issues.extend(validate_policy(scope, policy, datasets))
    return issues


if __name__ == "__main__":
    registry_issues = validate_registry()
    for issue in registry_issues:
        print(f"  - {issue}")
    raise SystemExit(1 if registry_issues else 0)
