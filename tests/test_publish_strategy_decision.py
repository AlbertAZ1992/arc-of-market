from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import pytest
import requests
from scripts import publish_strategy_decision
from scripts.publish_strategy_decision import (
    SigningRequest,
    endpoint_url,
    publication_status,
    publish,
    signing_headers,
    status_path,
    wait_for_completion,
)


def test_publication_retries_transient_errors_with_the_same_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "release.json"
    release_id = f"mr_{'a' * 64}"
    path.write_text(json.dumps({"releaseId": release_id}), encoding="utf-8")
    calls: list[str] = []
    delays: list[int] = []

    def post(_endpoint: str, _body: bytes, identity: str) -> requests.Response:
        calls.append(identity)
        response = requests.Response()
        response.status_code = 503 if len(calls) == 1 else 201
        response._content = b'{"status":"accepted"}'
        return response

    monkeypatch.setattr(publish_strategy_decision, "post_release", post)
    monkeypatch.setattr(publish_strategy_decision.time, "sleep", delays.append)
    assert publish("https://closing.example", path) == release_id
    assert calls == [release_id, release_id]
    assert delays == [10]


def test_publication_does_not_retry_contract_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "release.json"
    path.write_text(json.dumps({"releaseId": f"mr_{'a' * 64}"}), encoding="utf-8")
    response = requests.Response()
    response.status_code = 400
    response._content = b'{"code":"CONTRACT_INVALID"}'
    monkeypatch.setattr(publish_strategy_decision, "post_release", lambda *_: response)
    delays: list[int] = []
    monkeypatch.setattr(publish_strategy_decision.time, "sleep", delays.append)
    with pytest.raises(RuntimeError, match="rejected.*400.*CONTRACT_INVALID"):
        publish("https://closing.example", path)
    assert delays == []


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
