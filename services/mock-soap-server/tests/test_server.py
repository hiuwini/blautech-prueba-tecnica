from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID
import json
import unittest
import xml.etree.ElementTree as ET

from app.http.server import create_server
from app.soap import (
    COMPLIANCE_NS,
    SOAP_ENV_NS,
    SoapFaultError,
    SoapRequestError,
    build_compliance_response,
    build_fault,
    parse_compliance_request,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def text_by_local_name(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local_name and element.text:
            return element.text.strip()
    return None


class SoapXmlTests(unittest.TestCase):
    def test_parse_request_reads_document_type_and_document_id(self) -> None:
        request = parse_compliance_request(load_fixture("financial_report_request.xml"))

        self.assertEqual(request.document_type, "financial_report")
        self.assertEqual(request.document_id, "11111111-1111-4111-8111-111111111111")

    def test_response_maps_supported_document_types(self) -> None:
        expected_statuses = {
            "financial_report_request.xml": "COMPLIANT",
            "tax_filing_request.xml": "NON_COMPLIANT",
        }

        for fixture_name, expected_status in expected_statuses.items():
            with self.subTest(fixture_name=fixture_name):
                request = parse_compliance_request(load_fixture(fixture_name))
                response_xml = build_compliance_response(request)
                root = ET.fromstring(response_xml)

                self.assertEqual(root.tag, f"{{{SOAP_ENV_NS}}}Envelope")
                self.assertEqual(text_by_local_name(root, "DocumentType"), request.document_type)
                self.assertEqual(text_by_local_name(root, "DocumentId"), request.document_id)
                self.assertEqual(text_by_local_name(root, "Status"), expected_status)
                UUID(text_by_local_name(root, "CheckId") or "")

                checked_at = text_by_local_name(root, "CheckedAt")
                self.assertIsNotNone(checked_at)
                parsed_checked_at = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
                self.assertEqual(parsed_checked_at.tzinfo, timezone.utc)

    def test_regulatory_disclosure_is_compliant(self) -> None:
        request_xml = b"""
        <soapenv:Envelope
          xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
          xmlns:com="http://gov.example/regulatory/compliance">
          <soapenv:Body>
            <com:ComplianceCheckRequest>
              <com:DocumentType>regulatory_disclosure</com:DocumentType>
            </com:ComplianceCheckRequest>
          </soapenv:Body>
        </soapenv:Envelope>
        """

        request = parse_compliance_request(request_xml)
        response_xml = build_compliance_response(request)
        root = ET.fromstring(response_xml)

        self.assertEqual(text_by_local_name(root, "Status"), "COMPLIANT")

    def test_unsupported_document_type_generates_soap_fault(self) -> None:
        request = parse_compliance_request(load_fixture("invalid_document_type_request.xml"))

        with self.assertRaises(SoapFaultError):
            build_compliance_response(request)

        fault_xml = build_fault("Unsupported DocumentType: annual_statement")
        fault_root = ET.fromstring(fault_xml)

        self.assertEqual(text_by_local_name(fault_root, "faultcode"), "soapenv:Client")
        self.assertEqual(
            text_by_local_name(fault_root, "faultstring"),
            "Unsupported DocumentType: annual_statement",
        )

    def test_invalid_xml_payload_raises_request_error(self) -> None:
        with self.assertRaises(SoapRequestError):
            parse_compliance_request(b"<not-valid")

    def test_fixtures_are_valid_xml(self) -> None:
        for fixture_path in FIXTURES_DIR.glob("*.xml"):
            with self.subTest(fixture_path=fixture_path.name):
                root = ET.fromstring(fixture_path.read_bytes())
                self.assertEqual(root.tag, f"{{{SOAP_ENV_NS}}}Envelope")
                self.assertIsNotNone(root.find(f".//{{{COMPLIANCE_NS}}}DocumentType"))


class HttpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_health_endpoint_returns_ok(self) -> None:
        with urlopen(f"http://127.0.0.1:{self.port}/health", timeout=2) as response:
            body = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["service"], "mock-soap-server")

    def test_compliance_endpoint_returns_soap_response(self) -> None:
        request = Request(
            f"http://127.0.0.1:{self.port}/soap/compliance",
            data=load_fixture("financial_report_request.xml"),
            headers={"Content-Type": "text/xml; charset=utf-8"},
            method="POST",
        )

        with urlopen(request, timeout=2) as response:
            response_xml = response.read()

        root = ET.fromstring(response_xml)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers["Content-Type"], "text/xml; charset=utf-8")
        self.assertEqual(text_by_local_name(root, "Status"), "COMPLIANT")

    def test_compliance_endpoint_returns_soap_fault_for_invalid_document_type(self) -> None:
        request = Request(
            f"http://127.0.0.1:{self.port}/soap/compliance",
            data=load_fixture("invalid_document_type_request.xml"),
            headers={"Content-Type": "text/xml; charset=utf-8"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as error_context:
            urlopen(request, timeout=2)

        error = error_context.exception
        try:
            fault_body = error.read()
        finally:
            error.close()

        self.assertEqual(error.code, 500)
        fault_root = ET.fromstring(fault_body)
        self.assertEqual(
            text_by_local_name(fault_root, "faultstring"),
            "Unsupported DocumentType: annual_statement",
        )

    def test_compliance_endpoint_returns_soap_fault_when_document_type_is_missing(self) -> None:
        request_body = b"""
        <soapenv:Envelope
          xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
          xmlns:com="http://gov.example/regulatory/compliance">
          <soapenv:Body>
            <com:ComplianceCheckRequest>
              <com:DocumentId>11111111-1111-4111-8111-111111111111</com:DocumentId>
            </com:ComplianceCheckRequest>
          </soapenv:Body>
        </soapenv:Envelope>
        """
        request = Request(
            f"http://127.0.0.1:{self.port}/soap/compliance",
            data=request_body,
            headers={"Content-Type": "text/xml; charset=utf-8"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as error_context:
            urlopen(request, timeout=2)

        error = error_context.exception
        try:
            fault_body = error.read()
        finally:
            error.close()

        self.assertEqual(error.code, 400)
        fault_root = ET.fromstring(fault_body)
        self.assertEqual(text_by_local_name(fault_root, "faultcode"), "soapenv:Client")
        self.assertEqual(text_by_local_name(fault_root, "faultstring"), "DocumentType is required")


if __name__ == "__main__":
    unittest.main()
