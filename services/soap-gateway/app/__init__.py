from __future__ import annotations

from flask import Flask

from app.api.health import health_blueprint
from app.api.v1.compliance.blueprint import compliance_blueprint
from app.clients.mock_soap_client import MockSoapClient
from app.core.config import GatewayConfig
from app.repositories.mongo_processing_event_repository import (
    MongoProcessingEventRepository,
)
from app.repositories.postgres_compliance_repository import (
    PostgresComplianceRepository,
)
from app.services.compliance_service import ComplianceService


def create_app(
    config: GatewayConfig | None = None,
    soap_client: object | None = None,
    compliance_repository: object | None = None,
    event_repository: object | None = None,
) -> Flask:
    app_config = config or GatewayConfig.from_env()

    app = Flask(__name__)
    app.config["GATEWAY_CONFIG"] = app_config

    if soap_client is None:
        soap_client = MockSoapClient(
            base_url=app_config.mock_soap_base_url,
            timeout_seconds=app_config.mock_soap_timeout_seconds,
        )

    if compliance_repository is None:
        compliance_repository = PostgresComplianceRepository(app_config)

    if event_repository is None:
        event_repository = MongoProcessingEventRepository(app_config)

    app.extensions["soap_client"] = soap_client
    app.extensions["compliance_repository"] = compliance_repository
    app.extensions["event_repository"] = event_repository
    app.extensions["compliance_service"] = ComplianceService(
        soap_client=soap_client,
        compliance_repository=compliance_repository,
        event_repository=event_repository,
    )

    app.register_blueprint(health_blueprint)
    app.register_blueprint(compliance_blueprint)
    return app
