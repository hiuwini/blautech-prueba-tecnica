from __future__ import annotations

import xml.etree.ElementTree as ET

from defusedxml import ElementTree as SafeET

from app.core.statuses import COMPLIANT, NON_COMPLIANT
from app.soap.faults import SoapFaultError, SoapParseError
from app.soap.models import ComplianceSoapResult
from app.soap.namespaces import local_name


def parse_compliance_response(xml_body: str) -> ComplianceSoapResult:
    root = _safe_parse_xml(xml_body)
    fault = _find_first_by_local_name(root, "Fault")
    if fault is not None:
        raise SoapFaultError(
            fault_code=_find_text_by_local_name(fault, "faultcode") or "soapenv:Server",
            fault_string=_find_text_by_local_name(fault, "faultstring")
            or "Unknown SOAP Fault",
        )

    status = _required_text(root, "Status")
    if status not in {COMPLIANT, NON_COMPLIANT}:
        raise SoapParseError(f"Unsupported compliance status: {status}")

    return ComplianceSoapResult(
        document_id=_find_text_by_local_name(root, "DocumentId"),
        status=status,
        check_id=_required_text(root, "CheckId"),
        checked_at=_required_text(root, "CheckedAt"),
        details=_required_text(root, "Details"),
    )


def _safe_parse_xml(xml_body: str) -> ET.Element:
    try:
        return SafeET.fromstring(xml_body.encode("utf-8"))
    except Exception as exc:
        raise SoapParseError("Invalid SOAP XML response") from exc


def _required_text(root: ET.Element, local_name_value: str) -> str:
    value = _find_text_by_local_name(root, local_name_value)
    if value is None:
        raise SoapParseError(f"{local_name_value} is required in SOAP response")

    return value


def _find_first_by_local_name(root: ET.Element, local_name_value: str) -> ET.Element | None:
    for element in root.iter():
        if local_name(element.tag) == local_name_value:
            return element
    return None


def _find_text_by_local_name(root: ET.Element, local_name_value: str) -> str | None:
    element = _find_first_by_local_name(root, local_name_value)
    if element is None or element.text is None:
        return None

    value = element.text.strip()
    return value or None
