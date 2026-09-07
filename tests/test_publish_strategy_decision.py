from __future__ import annotations

import hashlib
import hmac

import pytest
from scripts.publish_strategy_decision import endpoint_url, signing_headers


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
        idempotency_key="strategy:mr_example",
        key_id="github-production",
        secret="secret",
        timestamp="1700000000",
    )

    assert headers["Content-SHA256"] == digest
    assert headers["X-Arc-Key-Id"] == "github-production"
    assert headers["X-Arc-Signature"] == expected
