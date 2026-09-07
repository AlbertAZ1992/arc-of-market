from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

STRATEGY_PATH = "/internal/v1/strategy-decisions"


def endpoint_url(base: str) -> str:
    endpoint = urljoin(base.rstrip("/") + "/", STRATEGY_PATH.lstrip("/"))
    parsed = urlparse(endpoint)
    is_local = parsed.hostname in {"localhost", "127.0.0.1"}
    if parsed.scheme != "https" and not (is_local and parsed.scheme == "http"):
        msg = "The endpoint must use HTTPS, except for localhost"
        raise ValueError(msg)
    return endpoint


def signing_headers(
    body: bytes,
    *,
    idempotency_key: str,
    key_id: str,
    secret: str,
    timestamp: str,
) -> dict[str, str]:
    digest = hashlib.sha256(body).hexdigest()
    base = "\n".join([timestamp, "POST", STRATEGY_PATH, idempotency_key, digest])
    signature = hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    return {
        "Content-SHA256": digest,
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
        "X-Arc-Key-Id": key_id,
        "X-Arc-Signature": signature,
        "X-Arc-Timestamp": timestamp,
    }


def required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def publish(endpoint: str, release_path: Path) -> None:
    body = release_path.read_bytes()
    release = json.loads(body)
    release_id = release.get("releaseId")
    if not isinstance(release_id, str) or not release_id.startswith("mr_"):
        raise ValueError("The release file is not a Market Release")
    headers = signing_headers(
        body,
        idempotency_key=f"strategy:{release_id}",
        key_id=required_environment("ARC_INGEST_KEY_ID"),
        secret=required_environment("ARC_INGEST_SECRET"),
        timestamp=str(int(time.time())),
    )
    response = requests.post(endpoint_url(endpoint), data=body, headers=headers, timeout=20)
    if not response.ok:
        raise RuntimeError(f"Strategy publication failed ({response.status_code}): {response.text}")
    print(response.text)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a signed strategy decision")
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--release", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    options = arguments()
    publish(options.endpoint, options.release)
