from __future__ import annotations

import xml.etree.ElementTree as ET

from app.soap.faults import SoapRequestError
from app.soap.models import ComplianceRequest
from app.soap.namespaces import local_name


def parse_compliance_request(xml_body: bytes | str) -> ComplianceRequest:
    try:
        root = ET.fromstring(xml_body)
    except ET.ParseError as exc:
        raise SoapRequestError("Invalid XML payload") from exc

    document_type = _find_text_by_local_name(root, "DocumentType")
    if not document_type:
        raise SoapRequestError("DocumentType is required")

    document_id = _find_text_by_local_name(root, "DocumentId")
    return ComplianceRequest(document_type=document_type, document_id=document_id)


def _find_text_by_local_name(root: ET.Element, local_name_value: str) -> str | None:
    for element in root.iter():
        if local_name(element.tag) == local_name_value and element.text:
            return element.text.strip()
    return None
