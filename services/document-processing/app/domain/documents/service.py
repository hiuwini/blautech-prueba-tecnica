from __future__ import annotations

from dataclasses import dataclass
import logging
from uuid import uuid4

from app.core.config import DocumentProcessingConfig
from app.core.errors import (
    ComplianceGatewayError,
    DocumentNotFoundError,
    PersistenceError,
    WebhookError,
)
from app.core.statuses import FAILED, PROCESSING
from app.core.time import to_iso_z, utc_now
from app.domain.compliance.models import ComplianceGatewayResult, ComplianceSummary
from app.domain.documents.models import DocumentRecord
from app.domain.documents.validators import (
    sanitize_filename,
    validate_non_empty_string,
    validate_uuid,
)


LOGGER = logging.getLogger(__name__)


class InvalidDocumentStateError(RuntimeError):
    """Raised when a requested document transition is not allowed."""


class DocumentReadError(RuntimeError):
    """Raised when the document cannot be read before processing."""


class DocumentProcessingStartError(RuntimeError):
    """Raised when the document cannot be marked as processing."""


class DocumentProcessingResultError(RuntimeError):
    """Raised when the final processing result cannot be persisted."""


@dataclass(frozen=True)
class DocumentListResult:
    records: list[DocumentRecord]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class DocumentDetailResult:
    record: DocumentRecord
    latest_check: ComplianceSummary | None = None


@dataclass(frozen=True)
class ProcessDocumentResult:
    document: DocumentRecord
    compliance_result: ComplianceGatewayResult | None
    notification_sent: bool | None
    gateway_error: ComplianceGatewayError | None = None


@dataclass(frozen=True)
class DownloadUrlResult:
    document_id: str
    url: str
    expires_in_seconds: int


class DocumentService:
    def __init__(
        self,
        *,
        config: DocumentProcessingConfig,
        document_repository: object,
        audit_repository: object,
        processing_event_repository: object,
        storage: object,
        compliance_client: object,
        webhook_client: object,
    ) -> None:
        self.config = config
        self.document_repository = document_repository
        self.audit_repository = audit_repository
        self.processing_event_repository = processing_event_repository
        self.storage = storage
        self.compliance_client = compliance_client
        self.webhook_client = webhook_client

    def upload_document(
        self,
        *,
        file_content: bytes,
        filename: str | None,
        content_type: str | None,
        document_type: str,
        user_id: str | None,
    ) -> DocumentRecord:
        normalized_type = validate_non_empty_string(document_type, "document_type")
        normalized_user_id: str | None = None
        if user_id is not None and user_id.strip():
            normalized_user_id = validate_uuid(user_id, "user_id")

        original_filename = sanitize_filename(filename)
        document_id = str(uuid4())
        object_key = f"documents/{document_id}/{original_filename}"
        bucket_name = self.config.minio_bucket
        effective_content_type = content_type or "application/octet-stream"

        self.storage.put_document(
            bucket_name=bucket_name,
            object_key=object_key,
            content=file_content,
            content_type=effective_content_type,
        )
        record = self.document_repository.create_document(
            document_id=document_id,
            user_id=normalized_user_id,
            document_type=normalized_type,
            original_filename=original_filename,
            content_type=effective_content_type,
            size_bytes=len(file_content),
            bucket_name=bucket_name,
            object_key=object_key,
        )
        self.audit_repository.insert_document_uploaded(
            document_id=record.document_id,
            user_id=record.user_id,
            metadata={
                "document_type": record.document_type,
                "original_filename": record.original_filename,
                "content_type": record.content_type,
                "size_bytes": record.size_bytes,
                "bucket_name": record.bucket_name,
                "object_key": record.object_key,
            },
            created_at=record.created_at,
        )
        return record

    def list_documents(self, *, limit: int, offset: int) -> DocumentListResult:
        records, total = self.document_repository.list_documents(
            limit=limit,
            offset=offset,
        )
        return DocumentListResult(records=records, total=total, limit=limit, offset=offset)

    def get_document_detail(self, document_id: str) -> DocumentDetailResult | None:
        normalized_document_id = validate_uuid(document_id, "document_id")
        record = self.document_repository.get_document(normalized_document_id)
        if record is None:
            return None

        latest_check = self.document_repository.get_latest_compliance(
            normalized_document_id
        )
        return DocumentDetailResult(record=record, latest_check=latest_check)

    def process_document(self, document_id: str) -> ProcessDocumentResult | None:
        normalized_document_id = validate_uuid(document_id, "document_id")
        try:
            current_record = self.document_repository.get_document(normalized_document_id)
        except PersistenceError as exc:
            raise DocumentReadError("Unable to read document") from exc

        if current_record is None:
            return None

        if current_record.status == PROCESSING:
            raise InvalidDocumentStateError("Document is already processing")

        try:
            processing_record = self.document_repository.update_status(
                document_id=normalized_document_id,
                status=PROCESSING,
                processed_at=None,
            )
            self.processing_event_repository.insert_event(
                document_id=normalized_document_id,
                status=PROCESSING,
                message="Document processing started",
                created_at=utc_now(),
                metadata={
                    "document_type": current_record.document_type,
                    "source": "document-processing",
                },
            )
        except DocumentNotFoundError:
            raise
        except PersistenceError as exc:
            raise DocumentProcessingStartError(
                "Unable to mark document as processing"
            ) from exc

        gateway_error: ComplianceGatewayError | None = None
        compliance_result: ComplianceGatewayResult | None = None
        final_status = FAILED

        try:
            compliance_result = self.compliance_client.check_document(
                document_id=normalized_document_id,
                document_type=processing_record.document_type,
            )
            final_status = compliance_result.status
        except ComplianceGatewayError as exc:
            gateway_error = exc
            final_status = FAILED

        completed_at = utc_now()
        try:
            final_record = self.document_repository.update_status(
                document_id=normalized_document_id,
                status=final_status,
                processed_at=completed_at,
            )
            self.processing_event_repository.insert_event(
                document_id=normalized_document_id,
                status=final_status,
                message=_final_event_message(final_status, gateway_error),
                created_at=completed_at,
                check_id=compliance_result.check_id if compliance_result else None,
                metadata={
                    "document_type": current_record.document_type,
                    "source": "document-processing",
                    "gateway_error": str(gateway_error) if gateway_error else None,
                },
            )
        except DocumentNotFoundError:
            raise
        except PersistenceError as exc:
            raise DocumentProcessingResultError(
                "Unable to persist processing result"
            ) from exc

        notification_sent = self._notify_bff(
            document=final_record,
            checked_at=compliance_result.checked_at if compliance_result else None,
            check_id=compliance_result.check_id if compliance_result else None,
            details=compliance_result.details if compliance_result else None,
        )

        return ProcessDocumentResult(
            document=final_record,
            compliance_result=compliance_result,
            notification_sent=notification_sent,
            gateway_error=gateway_error,
        )

    def get_download_url(
        self,
        *,
        document_id: str,
        expires_in_seconds: int | None,
    ) -> DownloadUrlResult | None:
        normalized_document_id = validate_uuid(document_id, "document_id")
        effective_expiry = (
            expires_in_seconds
            if expires_in_seconds is not None
            else self.config.presigned_url_expiry_seconds
        )

        record = self.document_repository.get_document(normalized_document_id)
        if record is None:
            return None

        url = self.storage.presigned_download_url(
            bucket_name=record.bucket_name,
            object_key=record.object_key,
            expires_in_seconds=effective_expiry,
        )
        return DownloadUrlResult(
            document_id=normalized_document_id,
            url=url,
            expires_in_seconds=effective_expiry,
        )

    def _notify_bff(
        self,
        *,
        document: DocumentRecord,
        checked_at: str | None,
        check_id: str | None,
        details: str | None,
    ) -> bool | None:
        payload = {
            "document_id": document.document_id,
            "status": document.status,
            "document_type": document.document_type,
            "checked_at": checked_at or to_iso_z(document.processed_at),
            "check_id": check_id,
            "details": details,
        }

        try:
            return self.webhook_client.notify_processing_complete(payload)
        except WebhookError as exc:
            LOGGER.warning("Unable to notify BFF webhook: %s", exc)
            return False


def _final_event_message(
    final_status: str,
    gateway_error: ComplianceGatewayError | None,
) -> str:
    if gateway_error is not None:
        return "Document processing failed because SOAP Gateway was unavailable"
    if final_status == FAILED:
        return "Document processing completed with failed compliance"
    return "Document processing completed"
