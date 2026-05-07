from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.v1.compliance.serializers import (
    compliance_check_response,
    compliance_failure_response,
    latest_status_response,
)
from app.api.v1.compliance.validators import (
    ValidationError,
    validate_non_empty_string,
    validate_uuid,
)
from app.core.errors import DocumentNotFoundError, PersistenceError, UpstreamSoapError
from app.services.compliance_service import (
    InvalidSoapResponseError,
    SoapFaultResultError,
)


compliance_blueprint = Blueprint(
    "compliance",
    __name__,
    url_prefix="/api/v1/compliance",
)


@compliance_blueprint.post("/check")
def check_compliance() -> tuple[object, int]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("INVALID_REQUEST", "JSON object body is required", 400)

    try:
        document_id = validate_uuid(payload.get("document_id"), "document_id")
        document_type = validate_non_empty_string(
            payload.get("document_type"),
            "document_type",
        )
    except ValidationError as exc:
        return _error("INVALID_REQUEST", str(exc), 400)

    try:
        result = current_app.extensions["compliance_service"].check_compliance(
            document_id=document_id,
            document_type=document_type,
        )
    except UpstreamSoapError as exc:
        return _error("UPSTREAM_UNAVAILABLE", str(exc), 502)
    except SoapFaultResultError as exc:
        return jsonify(compliance_failure_response(exc.result)), exc.result.status_code
    except InvalidSoapResponseError as exc:
        return jsonify(compliance_failure_response(exc.result)), exc.result.status_code
    except DocumentNotFoundError:
        return _document_not_found(document_id)
    except PersistenceError:
        return _error("PERSISTENCE_ERROR", "Unable to persist compliance result", 500)

    return jsonify(compliance_check_response(result)), 200


@compliance_blueprint.get("/status/<document_id>")
def compliance_status(document_id: str) -> tuple[object, int]:
    try:
        normalized_document_id = validate_uuid(document_id, "document_id")
        record = current_app.extensions["compliance_service"].get_latest_status(
            normalized_document_id
        )
    except ValidationError as exc:
        return _error("INVALID_REQUEST", str(exc), 400)
    except PersistenceError:
        return _error("PERSISTENCE_ERROR", "Unable to read compliance status", 500)

    if record is None:
        return _error("NOT_FOUND", "Compliance status was not found", 404)

    return jsonify(latest_status_response(record)), 200


def _document_not_found(document_id: str) -> tuple[object, int]:
    return _error(
        "DOCUMENT_NOT_FOUND",
        "Document does not exist in PostgreSQL",
        404,
        document_id=document_id,
    )


def _error(
    code: str,
    message: str,
    status_code: int,
    **extra: object,
) -> tuple[object, int]:
    payload: dict[str, object] = {"error": code, "message": message}
    payload.update(extra)
    return jsonify(payload), status_code
