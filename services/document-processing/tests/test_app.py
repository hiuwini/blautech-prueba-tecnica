from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import sys
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from app import create_app
from app.core.config import DocumentProcessingConfig
from app.core.errors import ComplianceGatewayError
from app.core.statuses import COMPLIANT, FAILED, NON_COMPLIANT, PROCESSING, UPLOADED
from app.domain.compliance.models import ComplianceGatewayResult, ComplianceSummary
from app.domain.documents.models import DocumentRecord


NOW = datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc)


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[str, DocumentRecord] = {}
        self.latest_checks: dict[str, ComplianceSummary] = {}

    def create_document(
        self,
        *,
        document_id: str,
        user_id: str | None,
        document_type: str,
        original_filename: str,
        content_type: str,
        size_bytes: int,
        bucket_name: str,
        object_key: str,
    ) -> DocumentRecord:
        record = DocumentRecord(
            document_id=document_id,
            user_id=user_id,
            document_type=document_type,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            bucket_name=bucket_name,
            object_key=object_key,
            status=UPLOADED,
            created_at=NOW,
            updated_at=NOW,
            processed_at=None,
        )
        self.documents[document_id] = record
        return record

    def seed_document(
        self,
        *,
        status: str = UPLOADED,
        document_type: str = "financial_report",
    ) -> DocumentRecord:
        document_id = str(uuid4())
        record = DocumentRecord(
            document_id=document_id,
            user_id=None,
            document_type=document_type,
            original_filename="seed.pdf",
            content_type="application/pdf",
            size_bytes=12,
            bucket_name="regulatory-documents",
            object_key=f"documents/{document_id}/seed.pdf",
            status=status,
            created_at=NOW,
            updated_at=NOW,
            processed_at=None,
        )
        self.documents[document_id] = record
        return record

    def list_documents(self, *, limit: int, offset: int) -> tuple[list[DocumentRecord], int]:
        records = sorted(
            self.documents.values(),
            key=lambda record: (record.created_at, record.document_id),
            reverse=True,
        )
        return records[offset : offset + limit], len(records)

    def get_document(self, document_id: str) -> DocumentRecord | None:
        return self.documents.get(document_id)

    def update_status(
        self,
        *,
        document_id: str,
        status: str,
        processed_at: datetime | None,
    ) -> DocumentRecord:
        record = self.documents[document_id]
        updated = replace(
            record,
            status=status,
            processed_at=processed_at,
            updated_at=processed_at or NOW,
        )
        self.documents[document_id] = updated
        return updated

    def get_latest_compliance(self, document_id: str) -> ComplianceSummary | None:
        return self.latest_checks.get(document_id)


class FakeAuditRepository:
    def __init__(self) -> None:
        self.logs: list[dict[str, Any]] = []

    def insert_document_uploaded(self, **payload: Any) -> None:
        self.logs.append(payload)


class FakeProcessingEventRepository:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def insert_event(self, **payload: Any) -> None:
        self.events.append(payload)


class FakeStorage:
    def __init__(self) -> None:
        self.objects: list[dict[str, Any]] = []

    def put_document(self, **payload: Any) -> None:
        self.objects.append(payload)

    def presigned_download_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expires_in_seconds: int,
    ) -> str:
        return f"http://minio.local/{bucket_name}/{object_key}?expires={expires_in_seconds}"


class FakeComplianceClient:
    def __init__(
        self,
        result: ComplianceGatewayResult | None = None,
        error: ComplianceGatewayError | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, str]] = []

    def check_document(
        self,
        *,
        document_id: str,
        document_type: str,
    ) -> ComplianceGatewayResult:
        self.calls.append({"document_id": document_id, "document_type": document_type})
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


class FakeWebhookClient:
    def __init__(self, result: bool | None = True) -> None:
        self.result = result
        self.payloads: list[dict[str, Any]] = []

    def notify_processing_complete(self, payload: dict[str, Any]) -> bool | None:
        self.payloads.append(payload)
        return self.result


def config() -> DocumentProcessingConfig:
    return DocumentProcessingConfig(
        host="127.0.0.1",
        port=8000,
        postgres_host="postgres",
        postgres_port=5432,
        postgres_db="regulatory_platform",
        postgres_user="regulatory_user",
        postgres_password="local-password",
        mongo_uri="mongodb://mongo:27017/regulatory_audit",
        mongo_database="regulatory_audit",
        minio_endpoint="http://minio:9000",
        minio_public_endpoint=None,
        minio_bucket="regulatory-documents",
        minio_access_key="local_minio_user",
        minio_secret_key="local-password",
        minio_secure=False,
        minio_region="us-east-1",
        soap_gateway_base_url="http://soap-gateway:8001",
        soap_gateway_timeout_seconds=5.0,
        bff_webhook_url="http://bff-notifications:4000/api/v1/webhooks/processing-complete",
        bff_webhook_timeout_seconds=3.0,
        cors_allowed_origins=("http://localhost:3000",),
        presigned_url_expiry_seconds=900,
    )


def build_client(
    *,
    compliance_client: FakeComplianceClient | None = None,
    webhook_client: FakeWebhookClient | None = None,
) -> tuple[
    TestClient,
    FakeDocumentRepository,
    FakeAuditRepository,
    FakeProcessingEventRepository,
    FakeStorage,
    FakeComplianceClient,
    FakeWebhookClient,
]:
    document_repository = FakeDocumentRepository()
    audit_repository = FakeAuditRepository()
    event_repository = FakeProcessingEventRepository()
    storage = FakeStorage()
    effective_compliance_client = compliance_client or FakeComplianceClient(
        ComplianceGatewayResult(
            document_id="",
            status=COMPLIANT,
            check_id="22222222-2222-4222-8222-222222222222",
            details="Document is compliant",
            checked_at="2026-05-05T10:30:00Z",
        )
    )
    effective_webhook_client = webhook_client or FakeWebhookClient()
    app = create_app(
        config(),
        document_repository=document_repository,
        audit_repository=audit_repository,
        processing_event_repository=event_repository,
        storage=storage,
        compliance_client=effective_compliance_client,
        webhook_client=effective_webhook_client,
    )
    return (
        TestClient(app),
        document_repository,
        audit_repository,
        event_repository,
        storage,
        effective_compliance_client,
        effective_webhook_client,
    )


def test_health_returns_service_status() -> None:
    client, *_ = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "document-processing"}


def test_upload_stores_object_metadata_and_audit_log() -> None:
    client, repository, audit_repository, _, storage, _, _ = build_client()

    response = client.post(
        "/api/v1/documents/upload",
        data={"document_type": "financial_report"},
        files={"file": ("report.pdf", b"binary-pdf", "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    document_id = body["document_id"]
    assert body["status"] == UPLOADED
    assert body["document_type"] == "financial_report"
    assert body["original_filename"] == "report.pdf"
    assert body["size_bytes"] == len(b"binary-pdf")

    assert repository.documents[document_id].object_key == storage.objects[0]["object_key"]
    assert storage.objects[0]["bucket_name"] == "regulatory-documents"
    assert storage.objects[0]["content"] == b"binary-pdf"

    assert audit_repository.logs == [
        {
            "document_id": document_id,
            "user_id": None,
            "metadata": {
                "document_type": "financial_report",
                "original_filename": "report.pdf",
                "content_type": "application/pdf",
                "size_bytes": len(b"binary-pdf"),
                "bucket_name": "regulatory-documents",
                "object_key": storage.objects[0]["object_key"],
            },
            "created_at": NOW,
        }
    ]


def test_upload_rejects_missing_document_type() -> None:
    client, *_ = build_client()

    response = client.post(
        "/api/v1/documents/upload",
        data={"document_type": " "},
        files={"file": ("report.pdf", b"binary-pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": "INVALID_REQUEST",
        "message": "document_type is required",
    }


def test_list_and_detail_return_paginated_documents_with_latest_compliance() -> None:
    client, repository, *_ = build_client()
    upload_response = client.post(
        "/api/v1/documents/upload",
        data={"document_type": "financial_report"},
        files={"file": ("report.pdf", b"binary-pdf", "application/pdf")},
    )
    document_id = upload_response.json()["document_id"]
    repository.latest_checks[document_id] = ComplianceSummary(
        document_id=document_id,
        status=COMPLIANT,
        check_id="22222222-2222-4222-8222-222222222222",
        details="Document is compliant",
        checked_at=NOW,
    )

    list_response = client.get("/api/v1/documents?limit=10&offset=0")
    detail_response = client.get(f"/api/v1/documents/{document_id}")

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["items"][0]["document_id"] == document_id

    assert detail_response.status_code == 200
    assert detail_response.json()["latest_compliance_check"] == {
        "document_id": document_id,
        "status": COMPLIANT,
        "check_id": "22222222-2222-4222-8222-222222222222",
        "details": "Document is compliant",
        "checked_at": "2026-05-05T10:30:00Z",
    }


def test_get_document_rejects_invalid_uuid() -> None:
    client, *_ = build_client()

    response = client.get("/api/v1/documents/not-a-uuid")

    assert response.status_code == 400
    assert response.json() == {
        "error": "INVALID_REQUEST",
        "message": "document_id must be a valid UUID",
    }


def test_process_updates_state_calls_gateway_and_notifies_bff() -> None:
    compliance_result = ComplianceGatewayResult(
        document_id="ignored-by-route",
        status=COMPLIANT,
        check_id="22222222-2222-4222-8222-222222222222",
        details="Document is compliant",
        checked_at="2026-05-05T10:30:00Z",
    )
    client, repository, _, event_repository, _, compliance_client, webhook_client = (
        build_client(compliance_client=FakeComplianceClient(compliance_result))
    )
    document = repository.seed_document()

    response = client.post(f"/api/v1/documents/{document.document_id}/process")

    assert response.status_code == 200
    assert response.json()["document"]["status"] == COMPLIANT
    assert response.json()["notification_sent"] is True
    assert repository.documents[document.document_id].status == COMPLIANT
    assert compliance_client.calls == [
        {
            "document_id": document.document_id,
            "document_type": "financial_report",
        }
    ]
    assert [event["status"] for event in event_repository.events] == [
        PROCESSING,
        COMPLIANT,
    ]
    assert webhook_client.payloads == [
        {
            "document_id": document.document_id,
            "status": COMPLIANT,
            "document_type": "financial_report",
            "checked_at": "2026-05-05T10:30:00Z",
            "check_id": "22222222-2222-4222-8222-222222222222",
            "details": "Document is compliant",
        }
    ]


def test_process_propagates_non_compliant_result_and_notifies_bff() -> None:
    compliance_result = ComplianceGatewayResult(
        document_id="ignored-by-route",
        status=NON_COMPLIANT,
        check_id="33333333-3333-4333-8333-333333333333",
        details="Document is not compliant",
        checked_at="2026-05-05T10:45:00Z",
    )
    client, repository, _, event_repository, _, compliance_client, webhook_client = (
        build_client(compliance_client=FakeComplianceClient(compliance_result))
    )
    document = repository.seed_document(document_type="tax_filing")

    response = client.post(f"/api/v1/documents/{document.document_id}/process")
    body = response.json()

    assert response.status_code == 200
    assert body["document"]["status"] == NON_COMPLIANT
    assert body["compliance_check"] == {
        "document_id": document.document_id,
        "status": NON_COMPLIANT,
        "check_id": "33333333-3333-4333-8333-333333333333",
        "details": "Document is not compliant",
        "checked_at": "2026-05-05T10:45:00Z",
    }
    assert repository.documents[document.document_id].status == NON_COMPLIANT
    assert compliance_client.calls == [
        {
            "document_id": document.document_id,
            "document_type": "tax_filing",
        }
    ]
    assert [event["status"] for event in event_repository.events] == [
        PROCESSING,
        NON_COMPLIANT,
    ]
    assert webhook_client.payloads == [
        {
            "document_id": document.document_id,
            "status": NON_COMPLIANT,
            "document_type": "tax_filing",
            "checked_at": "2026-05-05T10:45:00Z",
            "check_id": "33333333-3333-4333-8333-333333333333",
            "details": "Document is not compliant",
        }
    ]


def test_process_returns_not_found_without_calling_gateway() -> None:
    client, _, _, event_repository, _, compliance_client, webhook_client = build_client()
    missing_document_id = str(uuid4())

    response = client.post(f"/api/v1/documents/{missing_document_id}/process")

    assert response.status_code == 404
    assert response.json() == {
        "error": "DOCUMENT_NOT_FOUND",
        "message": "Document was not found",
        "document_id": missing_document_id,
    }
    assert event_repository.events == []
    assert compliance_client.calls == []
    assert webhook_client.payloads == []


def test_process_rejects_document_already_processing() -> None:
    client, repository, *_ = build_client()
    document = repository.seed_document(status=PROCESSING)

    response = client.post(f"/api/v1/documents/{document.document_id}/process")

    assert response.status_code == 409
    assert response.json() == {
        "error": "INVALID_DOCUMENT_STATE",
        "message": "Document is already processing",
    }


def test_process_marks_failed_when_gateway_is_unavailable() -> None:
    compliance_client = FakeComplianceClient(
        error=ComplianceGatewayError("SOAP Gateway is unavailable")
    )
    client, repository, _, event_repository, _, _, webhook_client = build_client(
        compliance_client=compliance_client
    )
    document = repository.seed_document()

    response = client.post(f"/api/v1/documents/{document.document_id}/process")

    assert response.status_code == 502
    assert response.json()["error"] == "COMPLIANCE_GATEWAY_ERROR"
    assert response.json()["document"]["status"] == FAILED
    assert repository.documents[document.document_id].status == FAILED
    assert [event["status"] for event in event_repository.events] == [PROCESSING, FAILED]
    assert webhook_client.payloads[0]["status"] == FAILED


def test_download_url_returns_presigned_minio_url() -> None:
    client, repository, *_ = build_client()
    document = repository.seed_document()

    response = client.get(
        f"/api/v1/documents/{document.document_id}/download-url?expires_in_seconds=120"
    )

    assert response.status_code == 200
    assert response.json() == {
        "document_id": document.document_id,
        "url": (
            "http://minio.local/regulatory-documents/"
            f"{document.object_key}?expires=120"
        ),
        "expires_in_seconds": 120,
    }


def test_minio_storage_uses_public_endpoint_for_presigned_urls(monkeypatch) -> None:
    from app.infrastructure.storage.minio_document_storage import MinioDocumentStorage

    created_clients: list[Any] = []

    class FakeMinio:
        def __init__(
            self,
            endpoint: str,
            *,
            access_key: str,
            secret_key: str,
            secure: bool,
            region: str,
        ) -> None:
            self.endpoint = endpoint
            self.secure = secure
            self.region = region
            created_clients.append(self)

        def put_object(self, *args: Any, **kwargs: Any) -> None:
            self.put_object_args = args
            self.put_object_kwargs = kwargs

        def presigned_get_object(self, bucket_name: str, object_key: str, **_: Any) -> str:
            scheme = "https" if self.secure else "http"
            return f"{scheme}://{self.endpoint}/{bucket_name}/{object_key}"

    monkeypatch.setitem(sys.modules, "minio", SimpleNamespace(Minio=FakeMinio))
    storage = MinioDocumentStorage(
        replace(
            config(),
            minio_endpoint="http://minio:9000",
            minio_public_endpoint="http://localhost:9000",
        )
    )

    storage.put_document(
        bucket_name="regulatory-documents",
        object_key="documents/example.pdf",
        content=b"example",
        content_type="application/pdf",
    )
    url = storage.presigned_download_url(
        bucket_name="regulatory-documents",
        object_key="documents/example.pdf",
        expires_in_seconds=120,
    )

    assert created_clients[0].endpoint == "minio:9000"
    assert created_clients[0].region == "us-east-1"
    assert created_clients[1].endpoint == "localhost:9000"
    assert url == "http://localhost:9000/regulatory-documents/documents/example.pdf"
