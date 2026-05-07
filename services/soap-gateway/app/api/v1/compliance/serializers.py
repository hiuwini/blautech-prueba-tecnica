from __future__ import annotations

from app.core.time import to_iso_z
from app.services.compliance_service import ComplianceCheckResult, ComplianceFailureResult


def compliance_check_response(result: ComplianceCheckResult) -> dict[str, object]:
    return {
        "document_id": result.document_id,
        "status": result.status,
        "check_id": result.check_id,
        "details": result.details,
        "checked_at": to_iso_z(result.checked_at),
    }


def compliance_failure_response(result: ComplianceFailureResult) -> dict[str, object]:
    return {
        "error": result.error,
        "message": result.message,
        "document_id": result.document_id,
        "status": result.status,
        "check_id": result.check_id,
        "checked_at": to_iso_z(result.checked_at),
    }


def latest_status_response(record: dict[str, object]) -> dict[str, object]:
    return {
        "document_id": record["document_id"],
        "status": record["status"],
        "check_id": record["check_id"],
        "details": record["details"],
        "checked_at": to_iso_z(record["checked_at"]),
    }
