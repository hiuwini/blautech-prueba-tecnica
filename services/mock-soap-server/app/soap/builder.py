from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import xml.etree.ElementTree as ET

from app.soap.models import ComplianceRequest, ComplianceResult
from app.soap.namespaces import COMPLIANCE_NS, SOAP_ENV_NS, qualified
from app.soap.rules import resolve_document_status, resolve_status_details


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_compliance_response(request: ComplianceRequest) -> str:
    status = resolve_document_status(request.document_type)
    result = ComplianceResult(
        document_id=request.document_id,
        document_type=request.document_type,
        status=status,
        check_id=str(uuid4()),
        checked_at=utc_now_iso(),
        details=resolve_status_details(status),
    )
    return _serialize_xml(_build_response_envelope(result))


def build_fault(fault_string: str, fault_code: str = "soapenv:Client") -> str:
    envelope = ET.Element(qualified(SOAP_ENV_NS, "Envelope"))
    body = ET.SubElement(envelope, qualified(SOAP_ENV_NS, "Body"))
    fault = ET.SubElement(body, qualified(SOAP_ENV_NS, "Fault"))
    ET.SubElement(fault, "faultcode").text = fault_code
    ET.SubElement(fault, "faultstring").text = fault_string
    return _serialize_xml(envelope)


def _build_response_envelope(result: ComplianceResult) -> ET.Element:
    envelope = ET.Element(qualified(SOAP_ENV_NS, "Envelope"))
    body = ET.SubElement(envelope, qualified(SOAP_ENV_NS, "Body"))
    response = ET.SubElement(body, qualified(COMPLIANCE_NS, "ComplianceCheckResponse"))

    if result.document_id:
        ET.SubElement(response, qualified(COMPLIANCE_NS, "DocumentId")).text = result.document_id

    ET.SubElement(response, qualified(COMPLIANCE_NS, "DocumentType")).text = result.document_type
    ET.SubElement(response, qualified(COMPLIANCE_NS, "Status")).text = result.status
    ET.SubElement(response, qualified(COMPLIANCE_NS, "CheckId")).text = result.check_id
    ET.SubElement(response, qualified(COMPLIANCE_NS, "CheckedAt")).text = result.checked_at
    ET.SubElement(response, qualified(COMPLIANCE_NS, "Details")).text = result.details
    return envelope


def _serialize_xml(element: ET.Element) -> str:
    xml_body = ET.tostring(element, encoding="unicode", short_empty_elements=True)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_body}'
