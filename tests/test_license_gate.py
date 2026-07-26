import json
from pathlib import Path

from scripts.license_gate import validate_review


def test_license_gate_fails_closed(tmp_path: Path) -> None:
    review = tmp_path / "review.json"
    review.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "public_release_approved": False,
                "subscriber_release_approved": False,
                "reviewed_at": None,
                "reviewed_by": None,
                "approval_reference": None,
                "blockers": ["market data rights missing"],
            }
        ),
        encoding="utf-8",
    )

    issues = validate_review(review)

    assert "public release is not approved" in issues
    assert "blocker: market data rights missing" in issues


def test_license_gate_accepts_completed_review(tmp_path: Path) -> None:
    review = tmp_path / "review.json"
    review.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "public_release_approved": True,
                "subscriber_release_approved": False,
                "reviewed_at": "2026-07-26",
                "reviewed_by": "legal counsel",
                "approval_reference": "contract-register-42",
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )

    assert validate_review(review) == []


def test_license_gate_checks_subscriber_approval_separately(tmp_path: Path) -> None:
    review = tmp_path / "review.json"
    review.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "public_release_approved": True,
                "subscriber_release_approved": False,
                "reviewed_at": "2026-07-26",
                "reviewed_by": "legal counsel",
                "approval_reference": "contract-register-42",
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )

    assert validate_review(review, scope="subscriber") == ["subscriber release is not approved"]
