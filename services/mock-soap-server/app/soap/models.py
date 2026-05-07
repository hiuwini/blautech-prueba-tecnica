from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComplianceRequest:
    document_type: str
    document_id: str | None = None


@dataclass(frozen=True)
class ComplianceResult:
    document_type: str
    status: str
    check_id: str
    checked_at: str
    details: str
    document_id: str | None = None
