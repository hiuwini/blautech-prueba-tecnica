from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.errors import ComplianceGatewayError
from app.core.statuses import FAILED, FINAL_DOCUMENT_STATUSES
from app.domain.compliance.models import ComplianceGatewayResult


class SoapGatewayClient:
    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def check_document(
        self,
        *,
        document_id: str,
        document_type: str,
    ) -> ComplianceGatewayResult:
        request_body = json.dumps(
            {
                "document_id": document_id,
                "document_type": document_type,
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/v1/compliance/check",
            data=request_body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                status_code = response.status
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            status_code = exc.code
            try:
                response_body = exc.read().decode("utf-8")
            finally:
                exc.close()
        except URLError as exc:
            raise ComplianceGatewayError("SOAP Gateway is unavailable") from exc

        payload = _decode_json(response_body)
        if status_code >= 400 and payload.get("status") != FAILED:
            raise ComplianceGatewayError(
                str(payload.get("message") or "SOAP Gateway returned an error"),
                status_code=status_code,
                payload=payload,
            )

        status = payload.get("status")
        if status not in FINAL_DOCUMENT_STATUSES:
            raise ComplianceGatewayError(
                "SOAP Gateway returned an invalid document status",
                status_code=status_code,
                payload=payload,
            )

        response_document_id = str(payload.get("document_id") or document_id)
        if response_document_id != document_id:
            raise ComplianceGatewayError(
                "SOAP Gateway response document_id does not match request",
                status_code=status_code,
                payload=payload,
            )

        return ComplianceGatewayResult(
            document_id=response_document_id,
            status=str(status),
            check_id=_optional_string(payload.get("check_id")),
            details=_optional_string(payload.get("details") or payload.get("message")),
            checked_at=_optional_string(payload.get("checked_at")),
        )


def _decode_json(raw_body: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ComplianceGatewayError("SOAP Gateway returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise ComplianceGatewayError("SOAP Gateway returned an invalid JSON payload")

    return payload


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
