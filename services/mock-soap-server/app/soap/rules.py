from app.soap.faults import SoapFaultError


DOCUMENT_STATUS = {
    "financial_report": "COMPLIANT",
    "tax_filing": "NON_COMPLIANT",
    "regulatory_disclosure": "COMPLIANT",
}

STATUS_DETAILS = {
    "COMPLIANT": "Document is compliant",
    "NON_COMPLIANT": "Document is not compliant",
}


def resolve_document_status(document_type: str) -> str:
    status = DOCUMENT_STATUS.get(document_type)
    if status is None:
        raise SoapFaultError(f"Unsupported DocumentType: {document_type}")
    return status


def resolve_status_details(status: str) -> str:
    return STATUS_DETAILS[status]
