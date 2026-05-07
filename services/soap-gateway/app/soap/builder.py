from __future__ import annotations

import xml.etree.ElementTree as ET

from app.soap.namespaces import COMPLIANCE_NS, SOAP_ENV_NS, qualified


def build_compliance_check_request(document_id: str, document_type: str) -> str:
    envelope = ET.Element(qualified(SOAP_ENV_NS, "Envelope"))
    ET.SubElement(envelope, qualified(SOAP_ENV_NS, "Header"))
    body = ET.SubElement(envelope, qualified(SOAP_ENV_NS, "Body"))
    request = ET.SubElement(body, qualified(COMPLIANCE_NS, "ComplianceCheckRequest"))
    ET.SubElement(request, qualified(COMPLIANCE_NS, "DocumentId")).text = document_id
    ET.SubElement(request, qualified(COMPLIANCE_NS, "DocumentType")).text = document_type
    return _serialize_xml(envelope)


def _serialize_xml(element: ET.Element) -> str:
    xml_body = ET.tostring(element, encoding="unicode", short_empty_elements=True)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_body}'
