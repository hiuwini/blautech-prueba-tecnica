from __future__ import annotations

from pydantic import BaseModel, Field


class ComplianceCheckResponse(BaseModel):
    document_id: str
    status: str
    check_id: str
    details: str | None = None
    checked_at: str


class DocumentResponse(BaseModel):
    document_id: str
    user_id: str | None = None
    document_type: str
    original_filename: str
    content_type: str
    size_bytes: int
    bucket_name: str
    object_key: str
    status: str
    created_at: str
    updated_at: str
    processed_at: str | None = None
    latest_compliance_check: ComplianceCheckResponse | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class ProcessDocumentResponse(BaseModel):
    document: DocumentResponse
    compliance_check: ComplianceCheckResponse | None = None
    notification_sent: bool | None = None


class DownloadUrlResponse(BaseModel):
    document_id: str
    url: str
    expires_in_seconds: int
