from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as api_v1_router
from app.core.config import DocumentProcessingConfig
from app.domain.documents.service import DocumentService
from app.infrastructure.clients.bff_webhook_client import BffWebhookClient
from app.infrastructure.clients.soap_gateway_client import SoapGatewayClient
from app.infrastructure.mongo.audit_log_repository import MongoAuditLogRepository
from app.infrastructure.mongo.processing_event_repository import (
    MongoProcessingEventRepository,
)
from app.infrastructure.postgres.document_repository import PostgresDocumentRepository
from app.infrastructure.storage.minio_document_storage import MinioDocumentStorage


def create_app(
    config: DocumentProcessingConfig | None = None,
    *,
    document_repository: object | None = None,
    audit_repository: object | None = None,
    processing_event_repository: object | None = None,
    storage: object | None = None,
    compliance_client: object | None = None,
    webhook_client: object | None = None,
) -> FastAPI:
    app_config = config or DocumentProcessingConfig.from_env()

    app = FastAPI(
        title="Document Processing API",
        version="0.1.0",
    )
    app.state.config = app_config

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_config.cors_allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.state.document_repository = (
        document_repository or PostgresDocumentRepository(app_config)
    )
    app.state.audit_repository = audit_repository or MongoAuditLogRepository(app_config)
    app.state.processing_event_repository = (
        processing_event_repository or MongoProcessingEventRepository(app_config)
    )
    app.state.storage = storage or MinioDocumentStorage(app_config)
    app.state.compliance_client = compliance_client or SoapGatewayClient(
        base_url=app_config.soap_gateway_base_url,
        timeout_seconds=app_config.soap_gateway_timeout_seconds,
    )
    app.state.webhook_client = webhook_client or BffWebhookClient(
        webhook_url=app_config.bff_webhook_url,
        timeout_seconds=app_config.bff_webhook_timeout_seconds,
    )
    app.state.document_service = DocumentService(
        config=app_config,
        document_repository=app.state.document_repository,
        audit_repository=app.state.audit_repository,
        processing_event_repository=app.state.processing_event_repository,
        storage=app.state.storage,
        compliance_client=app.state.compliance_client,
        webhook_client=app.state.webhook_client,
    )

    app.include_router(health_router)
    app.include_router(api_v1_router)
    return app
