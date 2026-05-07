from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from app.soap import (
    SoapFaultError,
    SoapParseError,
    build_compliance_check_request,
    parse_compliance_response,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def text_by_local_name(root: ET.Element, local_name: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local_name and element.text:
            return element.text.strip()
    return None


def test_build_compliance_check_request_serializes_expected_fields() -> None:
    xml_body = build_compliance_check_request(
        document_id="11111111-1111-4111-8111-111111111111",
        document_type="financial_report",
    )

    root = ET.fromstring(xml_body)

    assert text_by_local_name(root, "DocumentId") == "11111111-1111-4111-8111-111111111111"
    assert text_by_local_name(root, "DocumentType") == "financial_report"


def test_parse_compliance_response_reads_result() -> None:
    result = parse_compliance_response(load_fixture("compliant_response.xml"))

    assert result.document_id == "11111111-1111-4111-8111-111111111111"
    assert result.status == "COMPLIANT"
    assert result.check_id == "22222222-2222-4222-8222-222222222222"
    assert result.checked_at == "2026-05-05T10:30:00Z"
    assert result.details == "Document is compliant"


def test_parse_compliance_response_raises_for_soap_fault() -> None:
    with pytest.raises(SoapFaultError) as error_context:
        parse_compliance_response(load_fixture("soap_fault.xml"))

    assert error_context.value.fault_code == "soapenv:Client"
    assert error_context.value.fault_string == "Unsupported DocumentType: annual_statement"
    assert error_context.value.is_client_fault is True


def test_parse_compliance_response_rejects_unknown_status() -> None:
    response_xml = load_fixture("compliant_response.xml").replace(
        "<com:Status>COMPLIANT</com:Status>",
        "<com:Status>PENDING_REVIEW</com:Status>",
    )

    with pytest.raises(SoapParseError) as error_context:
        parse_compliance_response(response_xml)

    assert str(error_context.value) == "Unsupported compliance status: PENDING_REVIEW"
