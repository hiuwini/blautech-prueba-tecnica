from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from app import create_app
from app.clients.mock_soap_client import SoapHttpResponse
from app.core.config import GatewayConfig
from app.core.errors import DocumentNotFoundError
from app.repositories.postgres_compliance_repository import ComplianceRecord


FIXTURES_DIR = Path(__file__).parent / "fixtures"
DOCUMENT_ID = "11111111-1111-4111-8111-111111111111"
CHECK_ID = "22222222-2222-4222-8222-222222222222"
OTHER_DOCUMENT_ID = "33333333-3333-4333-8333-333333333333"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def text_by_local_name(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local_name and element.text:
            return element.text.strip()
    return None


class FakeSoapClient:
    def __init__(self, response: SoapHttpResponse) -> None:
        self.response = response
        self.requests: list[str] = []

    def check_compliance(self, xml_body: str) -> SoapHttpResponse:
        self.requests.append(xml_body)
        return self.response


class FakeComplianceRepository:
    def __init__(self) -> None:
        self.saved: list[ComplianceRecord] = []
        self.latest: dict[str, object] | None = None

    def save_check(self, record: ComplianceRecord) -> None:
        self.saved.append(record)
        self.latest = {
            "document_id": record.document_id,
            "status": record.status,
            "check_id": record.check_id,
            "details": record.details,
            "checked_at": record.checked_at,
        }

    def get_latest_by_document_id(self, document_id: str) -> dict[str, object] | None:
        if self.latest and self.latest["document_id"] == document_id:
            return self.latest
        return None


class FakeEventRepository:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def insert_event(self, **event: object) -> None:
        self.events.append(event)


class MissingDocumentRepository(FakeComplianceRepository):
    def save_check(self, record: ComplianceRecord) -> None:
        raise DocumentNotFoundError("Document does not exist")


@pytest.fixture
def config() -> GatewayConfig:
    return GatewayConfig(
        host="127.0.0.1",
        port=8001,
        mock_soap_base_url="http://mock-soap-server:8090",
        mock_soap_timeout_seconds=5.0,
        postgres_host="postgres",
        postgres_port=5432,
        postgres_db="regulatory_platform",
        postgres_user="regulatory_user",
        postgres_password="local-password",
        mongo_uri="mongodb://mongo:27017/regulatory_audit",
        mongo_database="regulatory_audit",
    )


def build_client(
    config: GatewayConfig,
    soap_response: SoapHttpResponse,
) -> tuple[object, FakeSoapClient, FakeComplianceRepository, FakeEventRepository]:
    soap_client = FakeSoapClient(soap_response)
    compliance_repository = FakeComplianceRepository()
    event_repository = FakeEventRepository()
    app = create_app(
        config=config,
        soap_client=soap_client,
        compliance_repository=compliance_repository,
        event_repository=event_repository,
    )
    return app.test_client(), soap_client, compliance_repository, event_repository


def test_health_returns_service_status(config: GatewayConfig) -> None:
    client, _, _, _ = build_client(
        config,
        SoapHttpResponse(status_code=200, body=load_fixture("compliant_response.xml")),
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "soap-gateway"}


def test_check_compliance_builds_soap_persists_and_returns_json(
    config: GatewayConfig,
) -> None:
    client, soap_client, compliance_repository, event_repository = build_client(
        config,
        SoapHttpResponse(status_code=200, body=load_fixture("compliant_response.xml")),
    )

    response = client.post(
        "/api/v1/compliance/check",
        json={"document_id": DOCUMENT_ID, "document_type": "financial_report"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "document_id": DOCUMENT_ID,
        "status": "COMPLIANT",
        "check_id": CHECK_ID,
        "details": "Document is compliant",
        "checked_at": "2026-05-05T10:30:00Z",
    }

    request_root = ET.fromstring(soap_client.requests[0])
    assert text_by_local_name(request_root, "DocumentId") == DOCUMENT_ID
    assert text_by_local_name(request_root, "DocumentType") == "financial_report"

    assert len(compliance_repository.saved) == 1
    saved = compliance_repository.saved[0]
    assert saved.document_id == DOCUMENT_ID
    assert saved.check_id == CHECK_ID
    assert saved.status == "COMPLIANT"
    assert saved.raw_request_xml == soap_client.requests[0]
    assert saved.raw_response_xml == load_fixture("compliant_response.xml")

    assert event_repository.events == [
        {
            "document_id": DOCUMENT_ID,
            "status": "COMPLIANT",
            "message": "Compliance check completed",
            "check_id": CHECK_ID,
            "metadata": {"document_type": "financial_report", "source": "soap-gateway"},
            "created_at": datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
        }
    ]


def test_check_compliance_rejects_invalid_uuid(config: GatewayConfig) -> None:
    client, soap_client, compliance_repository, event_repository = build_client(
        config,
        SoapHttpResponse(status_code=200, body=load_fixture("compliant_response.xml")),
    )

    response = client.post(
        "/api/v1/compliance/check",
        json={"document_id": "not-a-uuid", "document_type": "financial_report"},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "INVALID_REQUEST",
        "message": "document_id must be a valid UUID",
    }
    assert soap_client.requests == []
    assert compliance_repository.saved == []
    assert event_repository.events == []


def test_check_compliance_maps_soap_fault_to_failed_result(
    config: GatewayConfig,
) -> None:
    client, _, compliance_repository, event_repository = build_client(
        config,
        SoapHttpResponse(status_code=500, body=load_fixture("soap_fault.xml")),
    )

    response = client.post(
        "/api/v1/compliance/check",
        json={"document_id": DOCUMENT_ID, "document_type": "annual_statement"},
    )
    body = response.get_json()

    assert response.status_code == 400
    assert body["error"] == "SOAP_FAULT"
    assert body["message"] == "Unsupported DocumentType: annual_statement"
    assert body["document_id"] == DOCUMENT_ID
    assert body["status"] == "FAILED"
    assert body["check_id"]
    assert body["checked_at"].endswith("Z")

    assert len(compliance_repository.saved) == 1
    saved = compliance_repository.saved[0]
    assert saved.status == "FAILED"
    assert saved.details == "Unsupported DocumentType: annual_statement"
    assert saved.raw_response_xml == load_fixture("soap_fault.xml")

    assert len(event_repository.events) == 1
    assert event_repository.events[0]["status"] == "FAILED"
    assert event_repository.events[0]["message"] == "Compliance check failed with SOAP Fault"


def test_check_compliance_rejects_mismatched_soap_document_id(
    config: GatewayConfig,
) -> None:
    mismatched_response = load_fixture("compliant_response.xml").replace(
        DOCUMENT_ID,
        OTHER_DOCUMENT_ID,
    )
    client, _, compliance_repository, event_repository = build_client(
        config,
        SoapHttpResponse(status_code=200, body=mismatched_response),
    )

    response = client.post(
        "/api/v1/compliance/check",
        json={"document_id": DOCUMENT_ID, "document_type": "financial_report"},
    )
    body = response.get_json()

    assert response.status_code == 502
    assert body["error"] == "INVALID_SOAP_RESPONSE"
    assert body["message"] == "Mock SOAP Server returned an invalid compliance response"
    assert body["document_id"] == DOCUMENT_ID
    assert body["status"] == "FAILED"
    assert body["check_id"]
    assert body["checked_at"].endswith("Z")

    assert len(compliance_repository.saved) == 1
    saved = compliance_repository.saved[0]
    assert saved.document_id == DOCUMENT_ID
    assert saved.status == "FAILED"
    assert saved.details == "SOAP response document_id does not match request"
    assert saved.raw_response_xml == mismatched_response

    assert len(event_repository.events) == 1
    assert event_repository.events[0]["status"] == "FAILED"
    assert (
        event_repository.events[0]["message"]
        == "Compliance check failed with invalid SOAP response"
    )


def test_check_compliance_returns_not_found_when_document_is_missing(
    config: GatewayConfig,
) -> None:
    soap_client = FakeSoapClient(
        SoapHttpResponse(status_code=200, body=load_fixture("compliant_response.xml"))
    )
    event_repository = FakeEventRepository()
    app = create_app(
        config=config,
        soap_client=soap_client,
        compliance_repository=MissingDocumentRepository(),
        event_repository=event_repository,
    )
    client = app.test_client()

    response = client.post(
        "/api/v1/compliance/check",
        json={"document_id": DOCUMENT_ID, "document_type": "financial_report"},
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "error": "DOCUMENT_NOT_FOUND",
        "message": "Document does not exist in PostgreSQL",
        "document_id": DOCUMENT_ID,
    }
    assert event_repository.events == []


def test_status_returns_latest_compliance_check(config: GatewayConfig) -> None:
    client, _, compliance_repository, _ = build_client(
        config,
        SoapHttpResponse(status_code=200, body=load_fixture("compliant_response.xml")),
    )
    compliance_repository.latest = {
        "document_id": DOCUMENT_ID,
        "status": "NON_COMPLIANT",
        "check_id": CHECK_ID,
        "details": "Document is not compliant",
        "checked_at": datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
    }

    response = client.get(f"/api/v1/compliance/status/{DOCUMENT_ID}")

    assert response.status_code == 200
    assert response.get_json() == {
        "document_id": DOCUMENT_ID,
        "status": "NON_COMPLIANT",
        "check_id": CHECK_ID,
        "details": "Document is not compliant",
        "checked_at": "2026-05-05T10:30:00Z",
    }


def test_status_returns_not_found_for_missing_document(config: GatewayConfig) -> None:
    client, _, _, _ = build_client(
        config,
        SoapHttpResponse(status_code=200, body=load_fixture("compliant_response.xml")),
    )

    response = client.get(f"/api/v1/compliance/status/{DOCUMENT_ID}")

    assert response.status_code == 404
    assert response.get_json() == {
        "error": "NOT_FOUND",
        "message": "Compliance status was not found",
    }
