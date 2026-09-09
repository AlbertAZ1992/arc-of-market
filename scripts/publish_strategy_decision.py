from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

STRATEGY_PATH = "/internal/v1/strategy-decisions"
DEFAULT_WAIT_TIMEOUT_SECONDS = 30 * 60
DEFAULT_POLL_INTERVAL_SECONDS = 10


@dataclass(frozen=True)
class SigningRequest:
    idempotency_key: str
    key_id: str
    secret: str
    timestamp: str
    method: str = "POST"
    path: str = STRATEGY_PATH


def service_url(base: str, path: str) -> str:
    endpoint = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    parsed = urlparse(endpoint)
    is_local = parsed.hostname in {"localhost", "127.0.0.1"}
    if parsed.scheme != "https" and not (is_local and parsed.scheme == "http"):
        msg = "The endpoint must use HTTPS, except for localhost"
        raise ValueError(msg)
    return endpoint


def endpoint_url(base: str) -> str:
    return service_url(base, STRATEGY_PATH)


def status_path(release_id: str) -> str:
    if not release_id.startswith("mr_") or len(release_id) != 67:
        raise ValueError("The release identity is invalid")
    return f"{STRATEGY_PATH}/{release_id}/status"


def signing_headers(body: bytes, request: SigningRequest) -> dict[str, str]:
    digest = hashlib.sha256(body).hexdigest()
    base = "\n".join(
        [
            request.timestamp,
            request.method.upper(),
            request.path,
            request.idempotency_key,
            digest,
        ]
    )
    signature = hmac.new(request.secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    return {
        "Content-SHA256": digest,
        "Content-Type": "application/json",
        "Idempotency-Key": request.idempotency_key,
        "X-Arc-Key-Id": request.key_id,
        "X-Arc-Signature": signature,
        "X-Arc-Timestamp": request.timestamp,
    }


def required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def publish(endpoint: str, release_path: Path) -> str:
    body = release_path.read_bytes()
    release = json.loads(body)
    release_id = release.get("releaseId")
    if not isinstance(release_id, str) or not release_id.startswith("mr_"):
        raise ValueError("The release file is not a Market Release")
    headers = signing_headers(
        body,
        SigningRequest(
            idempotency_key=f"strategy:{release_id}",
            key_id=required_environment("ARC_INGEST_KEY_ID"),
            secret=required_environment("ARC_INGEST_SECRET"),
            timestamp=str(int(time.time())),
        ),
    )
    response = requests.post(endpoint_url(endpoint), data=body, headers=headers, timeout=20)
    if not response.ok:
        raise RuntimeError(f"Strategy publication failed ({response.status_code}): {response.text}")
    print(response.text)
    return release_id


def publication_status(endpoint: str, release_id: str) -> dict[str, object]:
    path = status_path(release_id)
    headers = signing_headers(
        b"",
        SigningRequest(
            idempotency_key=f"strategy-status:{release_id}",
            key_id=required_environment("ARC_INGEST_KEY_ID"),
            secret=required_environment("ARC_INGEST_SECRET"),
            timestamp=str(int(time.time())),
            method="GET",
            path=path,
        ),
    )
    response = requests.get(service_url(endpoint, path), headers=headers, timeout=20)
    if not response.ok:
        raise RuntimeError(f"Publication status failed ({response.status_code}): {response.text}")
    try:
        value = response.json()
    except requests.JSONDecodeError as error:
        raise RuntimeError("Publication status response is not JSON") from error
    if not isinstance(value, dict):
        raise RuntimeError("Publication status response is invalid")
    return value


def wait_for_completion(
    endpoint: str,
    release_id: str,
    *,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> None:
    if timeout_seconds < 0 or poll_interval_seconds < 1:
        raise ValueError("Publication wait settings are invalid")
    deadline = time.monotonic() + timeout_seconds
    previous_progress = ""
    while True:
        status = publication_status(endpoint, release_id)
        progress = json.dumps(status, sort_keys=True, separators=(",", ":"))
        if progress != previous_progress:
            print(f"Publication progress: {progress}")
            previous_progress = progress
        state = status.get("status")
        if state == "COMPLETE":
            return
        if state == "FAILED":
            stage = status.get("stage", "UNKNOWN")
            error_code = status.get("errorCode", "UNKNOWN")
            raise RuntimeError(f"Publication failed at {stage}: {error_code}")
        if time.monotonic() >= deadline:
            stage = status.get("stage", "UNKNOWN")
            raise RuntimeError(f"Publication timed out at {stage}")
        time.sleep(poll_interval_seconds)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a signed strategy decision")
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--wait-timeout-seconds", type=int, default=DEFAULT_WAIT_TIMEOUT_SECONDS)
    parser.add_argument("--poll-interval-seconds", type=int, default=DEFAULT_POLL_INTERVAL_SECONDS)
    return parser.parse_args()


if __name__ == "__main__":
    options = arguments()
    published_release_id = publish(options.endpoint, options.release)
    wait_for_completion(
        options.endpoint,
        published_release_id,
        timeout_seconds=options.wait_timeout_seconds,
        poll_interval_seconds=options.poll_interval_seconds,
    )
