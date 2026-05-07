from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from app.core.errors import DocumentNotFoundError, PersistenceError, UpstreamSoapError
from app.core.statuses import FAILED
from app.core.time import parse_iso_utc, utc_now
from app.repositories.postgres_compliance_repository import ComplianceRecord
from app.soap.builder import build_compliance_check_request
from app.soap.faults import SoapFaultError, SoapParseError
from app.soap.models import ComplianceSoapResult
from app.soap.parser import parse_compliance_response


@dataclass(frozen=True)
class ComplianceCheckResult:
    document_id: str
    status: str
    check_id: str
    details: str
    checked_at: object


@dataclass(frozen=True)
class ComplianceFailureResult:
    error: str
    message: str
    document_id: str
    status: str
    check_id: str
    checked_at: object
    status_code: int


class InvalidSoapResponseError(RuntimeError):
    def __init__(self, result: ComplianceFailureResult) -> None:
        super().__init__("Mock SOAP Server returned an invalid compliance response")
        self.result = result


class SoapFaultResultError(RuntimeError):
    def __init__(self, result: ComplianceFailureResult) -> None:
        super().__init__(result.message)
        self.result = result


class ComplianceService:
    def __init__(
        self,
        *,
        soap_client: object,
        compliance_repository: object,
        event_repository: object,
    ) -> None:
        self.soap_client = soap_client
        self.compliance_repository = compliance_repository
        self.event_repository = event_repository

    def check_compliance(
        self,
        *,
        document_id: str,
        document_type: str,
    ) -> ComplianceCheckResult:
        raw_request_xml = build_compliance_check_request(
            document_id=document_id,
            document_type=document_type,
        )

        try:
            soap_response = self.soap_client.check_compliance(raw_request_xml)
        except UpstreamSoapError:
            raise

        try:
            result = parse_compliance_response(soap_response.body)
            _validate_successful_soap_response(
                result=result,
                document_id=document_id,
                status_code=soap_response.status_code,
            )
            checked_at = parse_iso_utc(result.checked_at)
            record = ComplianceRecord(
                document_id=document_id,
                check_id=result.check_id,
                status=result.status,
                details=result.details,
                checked_at=checked_at,
                raw_request_xml=raw_request_xml,
                raw_response_xml=soap_response.body,
            )
            self._persist_record_and_event(
                record=record,
                document_type=document_type,
                event_message="Compliance check completed",
            )
            return ComplianceCheckResult(
                document_id=document_id,
                status=result.status,
                check_id=result.check_id,
                details=result.details,
                checked_at=checked_at,
            )
        except SoapFaultError as exc:
            checked_at = utc_now()
            record = ComplianceRecord(
                document_id=document_id,
                check_id=str(uuid4()),
                status=FAILED,
                details=exc.fault_string,
                checked_at=checked_at,
                raw_request_xml=raw_request_xml,
                raw_response_xml=soap_response.body,
            )
            self._persist_record_and_event(
                record=record,
                document_type=document_type,
                event_message="Compliance check failed with SOAP Fault",
            )
            status_code = 400 if exc.is_client_fault else 502
            raise SoapFaultResultError(
                ComplianceFailureResult(
                    error="SOAP_FAULT",
                    message=exc.fault_string,
                    document_id=document_id,
                    status=FAILED,
                    check_id=record.check_id,
                    checked_at=checked_at,
                    status_code=status_code,
                )
            ) from exc
        except SoapParseError as exc:
            checked_at = utc_now()
            record = ComplianceRecord(
                document_id=document_id,
                check_id=str(uuid4()),
                status=FAILED,
                details=str(exc),
                checked_at=checked_at,
                raw_request_xml=raw_request_xml,
                raw_response_xml=soap_response.body,
            )
            self._persist_record_and_event(
                record=record,
                document_type=document_type,
                event_message="Compliance check failed with invalid SOAP response",
            )
            raise InvalidSoapResponseError(
                ComplianceFailureResult(
                    error="INVALID_SOAP_RESPONSE",
                    message="Mock SOAP Server returned an invalid compliance response",
                    document_id=document_id,
                    status=FAILED,
                    check_id=record.check_id,
                    checked_at=checked_at,
                    status_code=502,
                )
            ) from exc

    def get_latest_status(self, document_id: str) -> dict[str, object] | None:
        return self.compliance_repository.get_latest_by_document_id(document_id)

    def _persist_record_and_event(
        self,
        *,
        record: ComplianceRecord,
        document_type: str,
        event_message: str,
    ) -> None:
        self.compliance_repository.save_check(record)
        self.event_repository.insert_event(
            document_id=record.document_id,
            status=record.status,
            message=event_message,
            check_id=record.check_id,
            metadata={"document_type": document_type, "source": "soap-gateway"},
            created_at=record.checked_at,
        )


def _validate_successful_soap_response(
    *,
    result: ComplianceSoapResult,
    document_id: str,
    status_code: int,
) -> None:
    if status_code >= 400:
        raise SoapParseError("Mock SOAP Server returned HTTP error without SOAP Fault")

    if result.document_id and result.document_id != document_id:
        raise SoapParseError("SOAP response document_id does not match request")

    try:
        str(UUID(result.check_id))
        parse_iso_utc(result.checked_at)
    except ValueError as exc:
        raise SoapParseError("SOAP response contains invalid CheckId or CheckedAt") from exc


__all__ = [
    "ComplianceCheckResult",
    "ComplianceFailureResult",
    "ComplianceService",
    "DocumentNotFoundError",
    "InvalidSoapResponseError",
    "PersistenceError",
    "SoapFaultResultError",
    "UpstreamSoapError",
]
