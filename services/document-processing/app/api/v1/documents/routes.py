from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import JSONResponse

from app.api.v1.documents.dependencies import get_document_service
from app.api.v1.documents.schemas import (
    ComplianceCheckResponse,
    DocumentListResponse,
    DocumentResponse,
    DownloadUrlResponse,
    ProcessDocumentResponse,
)
from app.core.errors import (
    DocumentNotFoundError,
    InvalidReferenceError,
    PersistenceError,
    StorageError,
)
from app.core.time import to_iso_z
from app.domain.compliance.models import ComplianceGatewayResult, ComplianceSummary
from app.domain.documents.models import DocumentRecord
from app.domain.documents.service import (
    DocumentProcessingResultError,
    DocumentProcessingStartError,
    DocumentReadError,
    DocumentService,
    InvalidDocumentStateError,
)
from app.domain.documents.validators import ValidationError


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=201, response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    user_id: str | None = Form(default=None),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse | JSONResponse:
    try:
        record = document_service.upload_document(
            file_content=file.file.read(),
            filename=file.filename,
            content_type=file.content_type,
            document_type=document_type,
            user_id=user_id,
        )
    except ValidationError as exc:
        return _error("INVALID_REQUEST", exc.message, 400)
    except StorageError:
        return _error("OBJECT_STORAGE_ERROR", "Unable to store uploaded document", 502)
    except InvalidReferenceError:
        return _error("USER_NOT_FOUND", "Referenced user does not exist", 400)
    except PersistenceError:
        return _error("PERSISTENCE_ERROR", "Unable to persist document upload", 500)

    return _document_response(record)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse | JSONResponse:
    try:
        result = document_service.list_documents(limit=limit, offset=offset)
    except PersistenceError:
        return _error("PERSISTENCE_ERROR", "Unable to list documents", 500)

    return DocumentListResponse(
        items=[_document_response(record) for record in result.records],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse | JSONResponse:
    try:
        result = document_service.get_document_detail(document_id)
    except ValidationError as exc:
        return _error("INVALID_REQUEST", exc.message, 400)
    except PersistenceError:
        return _error("PERSISTENCE_ERROR", "Unable to read document", 500)

    if result is None:
        return _document_not_found(document_id)

    return _document_response(result.record, result.latest_check)


@router.post("/{document_id}/process", response_model=ProcessDocumentResponse)
def process_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> ProcessDocumentResponse | JSONResponse:
    try:
        result = document_service.process_document(document_id)
    except ValidationError as exc:
        return _error("INVALID_REQUEST", exc.message, 400)
    except DocumentReadError:
        return _error("PERSISTENCE_ERROR", "Unable to read document", 500)
    except InvalidDocumentStateError as exc:
        return _error("INVALID_DOCUMENT_STATE", str(exc), 409)
    except DocumentNotFoundError:
        return _document_not_found(document_id)
    except DocumentProcessingStartError:
        return _error("PERSISTENCE_ERROR", "Unable to mark document as processing", 500)
    except DocumentProcessingResultError:
        return _error("PERSISTENCE_ERROR", "Unable to persist processing result", 500)

    if result is None:
        return _document_not_found(document_id)

    response = ProcessDocumentResponse(
        document=_document_response(result.document),
        compliance_check=_compliance_result_response(
            result.document.document_id,
            result.compliance_result,
        ),
        notification_sent=result.notification_sent,
    )

    if result.gateway_error is not None:
        return _error(
            "COMPLIANCE_GATEWAY_ERROR",
            str(result.gateway_error),
            502,
            document=_schema_dict(response.document),
            compliance_check=None,
            notification_sent=result.notification_sent,
        )

    return response


@router.get("/{document_id}/download-url", response_model=DownloadUrlResponse)
def get_download_url(
    document_id: str,
    expires_in_seconds: int | None = Query(default=None, ge=60, le=3600),
    document_service: DocumentService = Depends(get_document_service),
) -> DownloadUrlResponse | JSONResponse:
    try:
        result = document_service.get_download_url(
            document_id=document_id,
            expires_in_seconds=expires_in_seconds,
        )
    except ValidationError as exc:
        return _error("INVALID_REQUEST", exc.message, 400)
    except PersistenceError:
        return _error("PERSISTENCE_ERROR", "Unable to read document", 500)
    except StorageError:
        return _error("OBJECT_STORAGE_ERROR", "Unable to create download URL", 502)

    if result is None:
        return _document_not_found(document_id)

    return DownloadUrlResponse(
        document_id=result.document_id,
        url=result.url,
        expires_in_seconds=result.expires_in_seconds,
    )


def _document_response(
    record: DocumentRecord,
    latest_check: ComplianceSummary | None = None,
) -> DocumentResponse:
    return DocumentResponse(
        document_id=record.document_id,
        user_id=record.user_id,
        document_type=record.document_type,
        original_filename=record.original_filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        bucket_name=record.bucket_name,
        object_key=record.object_key,
        status=record.status,
        created_at=to_iso_z(record.created_at) or "",
        updated_at=to_iso_z(record.updated_at) or "",
        processed_at=to_iso_z(record.processed_at),
        latest_compliance_check=(
            ComplianceCheckResponse(
                document_id=latest_check.document_id,
                status=latest_check.status,
                check_id=latest_check.check_id,
                details=latest_check.details,
                checked_at=to_iso_z(latest_check.checked_at) or "",
            )
            if latest_check
            else None
        ),
    )


def _compliance_result_response(
    document_id: str,
    compliance_result: ComplianceGatewayResult | None,
) -> ComplianceCheckResponse | None:
    if compliance_result is None:
        return None
    return ComplianceCheckResponse(
        document_id=document_id,
        status=compliance_result.status,
        check_id=compliance_result.check_id or "",
        details=compliance_result.details,
        checked_at=compliance_result.checked_at or "",
    )


def _document_not_found(document_id: str) -> JSONResponse:
    return _error(
        "DOCUMENT_NOT_FOUND",
        "Document was not found",
        404,
        document_id=document_id,
    )


def _error(
    code: str,
    message: str,
    status_code: int,
    **extra: Any,
) -> JSONResponse:
    payload: dict[str, Any] = {"error": code, "message": message}
    payload.update(extra)
    return JSONResponse(status_code=status_code, content=payload)


def _schema_dict(schema: Any) -> dict[str, Any]:
    if hasattr(schema, "model_dump"):
        return schema.model_dump()
    return schema.dict()
