from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComplianceSoapResult:
    status: str
    check_id: str
    checked_at: str
    details: str
    document_id: str | None = None
