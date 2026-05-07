from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ComplianceSummary:
    document_id: str
    status: str
    check_id: str
    details: str | None
    checked_at: datetime


@dataclass(frozen=True)
class ComplianceGatewayResult:
    document_id: str
    status: str
    check_id: str | None
    details: str | None
    checked_at: str | None
