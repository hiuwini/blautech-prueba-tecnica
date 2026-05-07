#!/usr/bin/env python3
"""End-to-end smoke test for the regulatory-platform stack.

Runs the upload -> process -> webhook flow via HTTP against the host-published
ports of `docker compose`. Stdlib only (no third-party dependencies).

Prerequisites:
  docker compose up -d                  # bring up the full stack
  # or, if you only need the backend (e.g. running Vite separately):
  # docker compose up -d \\
  #   postgres mongo minio minio-init \\
  #   mock-soap-server soap-gateway document-processing bff-notifications

Usage:
  python3 scripts/smoke_e2e.py
  python3 scripts/smoke_e2e.py --document-type tax_filing       # expects NON_COMPLIANT
  python3 scripts/smoke_e2e.py --document-type annual_statement # expects FAILED
  python3 scripts/smoke_e2e.py --base-fastapi http://localhost:8000 --base-bff http://localhost:4000
  python3 scripts/smoke_e2e.py --skip-frontend                  # ignore frontend health

Exit codes:
  0 success, 1 healthcheck failed, 2 upload failed, 3 process failed,
  4 webhook smoke failed, 5 unexpected status, 6 timeout polling status.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

DEFAULT_FASTAPI = os.environ.get("SMOKE_FASTAPI_URL", "http://localhost:8000")
DEFAULT_BFF = os.environ.get("SMOKE_BFF_URL", "http://localhost:4000")
DEFAULT_MOCK_SOAP = os.environ.get("SMOKE_MOCK_SOAP_URL", "http://localhost:8090")
DEFAULT_SOAP_GATEWAY = os.environ.get("SMOKE_SOAP_GATEWAY_URL", "http://localhost:8001")
DEFAULT_FRONTEND = os.environ.get("SMOKE_FRONTEND_URL", "http://localhost:3000")

EXPECTED_BY_TYPE = {
    "financial_report": "COMPLIANT",
    "regulatory_disclosure": "COMPLIANT",
    "tax_filing": "NON_COMPLIANT",
}


def log(message: str) -> None:
    print(f"[smoke-e2e] {message}", flush=True)


def http_get(url: str, timeout: float = 5.0) -> tuple[int, dict[str, Any] | None]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, _safe_json(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, _safe_json(body)
    except urllib.error.URLError as error:
        log(f"GET {url} failed: {error.reason}")
        return 0, None


def http_post_json(url: str, payload: dict[str, Any], timeout: float = 5.0) -> tuple[int, dict[str, Any] | None]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, _safe_json(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, _safe_json(body)


def http_post_multipart(
    url: str, file_field: str, file_name: str, file_bytes: bytes, content_type: str, fields: dict[str, str], timeout: float = 10.0
) -> tuple[int, dict[str, Any] | None]:
    boundary = f"----smoke{uuid.uuid4().hex}"
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(value.encode())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_name}"\r\n'.encode()
    )
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
            return response.status, _safe_json(text)
    except urllib.error.HTTPError as error:
        text = error.read().decode("utf-8", errors="replace")
        return error.code, _safe_json(text)


def _safe_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def http_get_text(url: str, timeout: float = 5.0) -> tuple[int, str | None]:
    request = urllib.request.Request(url, headers={"Accept": "text/plain"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        text = error.read().decode("utf-8", errors="replace")
        return error.code, text
    except urllib.error.URLError as error:
        log(f"GET {url} failed: {error.reason}")
        return 0, None


def healthchecks(args: argparse.Namespace) -> bool:
    targets = {
        "mock-soap-server": f"{args.base_mock_soap}/health",
        "soap-gateway": f"{args.base_soap_gateway}/health",
        "document-processing": f"{args.base_fastapi}/health",
        "bff-notifications": f"{args.base_bff}/health",
    }
    ok = True
    for name, url in targets.items():
        status, body = http_get(url)
        if status == 200 and body and body.get("status") == "ok":
            log(f"  health OK {name} -> {url}")
        else:
            log(f"  health FAIL {name} -> {url} (status={status}, body={body})")
            ok = False

    if not args.skip_frontend:
        url = f"{args.base_frontend}/health"
        status, text = http_get_text(url)
        if status == 200 and text and text.strip().lower().startswith("ok"):
            log(f"  health OK frontend -> {url}")
        else:
            log(f"  health FAIL frontend -> {url} (status={status}, body={text!r})")
            ok = False

    return ok


def upload(args: argparse.Namespace) -> dict[str, Any] | None:
    file_path = args.file
    if file_path:
        with open(file_path, "rb") as handle:
            payload = handle.read()
        file_name = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    else:
        payload = b"# smoke E2E payload\nGenerated by scripts/smoke_e2e.py\n"
        file_name = f"smoke_{uuid.uuid4().hex[:8]}.md"
        content_type = "text/markdown"

    url = f"{args.base_fastapi}/api/v1/documents/upload"
    status, body = http_post_multipart(
        url,
        file_field="file",
        file_name=file_name,
        file_bytes=payload,
        content_type=content_type,
        fields={"document_type": args.document_type},
    )
    if status not in (200, 201) or not body:
        log(f"upload failed: status={status}, body={body}")
        return None
    log(f"  uploaded document_id={body.get('document_id')} status={body.get('status')}")
    return body


def process_document(args: argparse.Namespace, document_id: str) -> dict[str, Any] | None:
    url = f"{args.base_fastapi}/api/v1/documents/{document_id}/process"
    status, body = http_post_json(url, {}, timeout=args.process_timeout)
    if status not in (200, 202) or not body:
        log(f"process failed: status={status}, body={body}")
        return body
    log(f"  process response status={body.get('document', {}).get('status')} notification_sent={body.get('notification_sent')}")
    return body


def poll_for_terminal_status(args: argparse.Namespace, document_id: str, expected: str | None) -> str | None:
    deadline = time.time() + args.poll_timeout
    last_status: str | None = None
    while time.time() < deadline:
        status, body = http_get(f"{args.base_fastapi}/api/v1/documents/{document_id}")
        if status == 200 and body:
            current = body.get("status")
            if current != last_status:
                log(f"  poll status -> {current}")
                last_status = current
            if current in {"COMPLIANT", "NON_COMPLIANT", "FAILED"}:
                if expected and current != expected:
                    log(f"unexpected terminal status: got {current}, expected {expected}")
                    return None
                return current
        time.sleep(1)
    log(f"timeout waiting for terminal status (last={last_status})")
    return None


def webhook_smoke(args: argparse.Namespace) -> bool:
    url = f"{args.base_bff}/api/v1/webhooks/processing-complete"
    payload = {
        "document_id": str(uuid.uuid4()),
        "status": "COMPLIANT",
        "document_type": "financial_report",
        "checked_at": "2026-05-06T10:30:00Z",
    }
    status, body = http_post_json(url, payload)
    if status == 202 and body and body.get("status") == "accepted":
        log(f"  webhook accepted event={body.get('event')}")
        return True
    log(f"webhook smoke failed: status={status}, body={body}")
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-fastapi", default=DEFAULT_FASTAPI, help="FastAPI base URL")
    parser.add_argument("--base-bff", default=DEFAULT_BFF, help="BFF base URL")
    parser.add_argument("--base-mock-soap", default=DEFAULT_MOCK_SOAP, help="Mock SOAP server base URL")
    parser.add_argument("--base-soap-gateway", default=DEFAULT_SOAP_GATEWAY, help="SOAP Gateway base URL")
    parser.add_argument("--base-frontend", default=DEFAULT_FRONTEND, help="Frontend base URL")
    parser.add_argument("--document-type", default="financial_report", help="DocumentType to upload")
    parser.add_argument("--file", default=None, help="Optional path to file to upload (default: synthetic markdown)")
    parser.add_argument("--process-timeout", type=float, default=15.0, help="Timeout for process call (seconds)")
    parser.add_argument("--poll-timeout", type=float, default=20.0, help="Timeout for status polling (seconds)")
    parser.add_argument("--skip-healthchecks", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend /health (useful when running Vite from host)")
    parser.add_argument("--skip-webhook", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    log(f"target FastAPI={args.base_fastapi} BFF={args.base_bff}")
    log(f"document_type={args.document_type}")

    expected = EXPECTED_BY_TYPE.get(args.document_type)
    if expected is None:
        log(f"  (no expected status for '{args.document_type}'; SOAP Fault path -> FAILED)")
        expected = "FAILED"

    if not args.skip_healthchecks:
        log("step 1/4 healthchecks")
        if not healthchecks(args):
            return 1

    log("step 2/4 upload")
    uploaded = upload(args)
    if not uploaded:
        return 2
    document_id = uploaded.get("document_id")
    if not document_id:
        return 2

    log("step 3/4 process + poll")
    process_response = process_document(args, document_id)
    if process_response is None:
        return 3
    final_status = poll_for_terminal_status(args, document_id, expected)
    if final_status is None:
        return 6
    if final_status != expected:
        return 5

    if not args.skip_webhook:
        log("step 4/4 webhook smoke")
        if not webhook_smoke(args):
            return 4

    log(f"OK final_status={final_status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
