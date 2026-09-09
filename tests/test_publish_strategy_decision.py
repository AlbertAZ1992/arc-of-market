from __future__ import annotations

import hashlib
import hmac

import pytest
from scripts import publish_strategy_decision
from scripts.publish_strategy_decision import (
    SigningRequest,
    endpoint_url,
    publication_status,
    signing_headers,
    status_path,
    wait_for_completion,
)


def test_endpoint_url_requires_https_except_for_localhost() -> None:
    assert endpoint_url("https://closing.example") == (
        "https://closing.example/internal/v1/strategy-decisions"
    )
    assert endpoint_url("http://localhost:8788") == (
        "http://localhost:8788/internal/v1/strategy-decisions"
    )
    with pytest.raises(ValueError, match="must use HTTPS"):
        endpoint_url("http://closing.example")


def test_signing_headers_match_the_cloud_contract() -> None:
    body = b'{"releaseId":"mr_example"}'
    digest = hashlib.sha256(body).hexdigest()
    base = f"1700000000\nPOST\n/internal/v1/strategy-decisions\nstrategy:mr_example\n{digest}"
    expected = hmac.new(b"secret", base.encode(), hashlib.sha256).hexdigest()

    headers = signing_headers(
        body,
        SigningRequest(
            idempotency_key="strategy:mr_example",
            key_id="github-production",
            secret="secret",
            timestamp="1700000000",
        ),
    )

    assert headers["Content-SHA256"] == digest
    assert headers["X-Arc-Key-Id"] == "github-production"
    assert headers["X-Arc-Signature"] == expected


def test_status_request_uses_signed_get(monkeypatch: pytest.MonkeyPatch) -> None:
    release_id = f"mr_{'a' * 64}"
    requested: dict[str, object] = {}

    class Response:
        ok = True

        def json(self) -> dict[str, str]:
            return {"status": "COMPLETE"}

    def fake_get(url: str, **kwargs: object) -> Response:
        requested.update(url=url, **kwargs)
        return Response()

    monkeypatch.setenv("ARC_INGEST_KEY_ID", "github-production")
    monkeypatch.setenv("ARC_INGEST_SECRET", "secret")
    monkeypatch.setattr(publish_strategy_decision.requests, "get", fake_get)

    assert publication_status("https://closing.example", release_id) == {"status": "COMPLETE"}
    assert requested["url"] == f"https://closing.example{status_path(release_id)}"
    headers = requested["headers"]
    assert isinstance(headers, dict)
    assert headers["X-Arc-Key-Id"] == "github-production"


def test_wait_for_completion_rejects_failed_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        publish_strategy_decision,
        "publication_status",
        lambda *_args: {
            "status": "FAILED",
            "stage": "EMAIL_DELIVERY",
            "errorCode": "EMAIL_DELIVERY_FAILED",
        },
    )

    with pytest.raises(RuntimeError, match="EMAIL_DELIVERY.*EMAIL_DELIVERY_FAILED"):
        wait_for_completion(
            "https://closing.example",
            f"mr_{'a' * 64}",
            timeout_seconds=0,
            poll_interval_seconds=1,
        )


def test_wait_for_completion_accepts_complete_zero_recipient_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        publish_strategy_decision,
        "publication_status",
        lambda *_args: {
            "status": "COMPLETE",
            "stage": "COMPLETE",
            "deliveries": {"planned": 0, "pending": 0, "sent": 0, "failed": 0},
        },
    )

    wait_for_completion(
        "https://closing.example",
        f"mr_{'a' * 64}",
        timeout_seconds=0,
        poll_interval_seconds=1,
    )
