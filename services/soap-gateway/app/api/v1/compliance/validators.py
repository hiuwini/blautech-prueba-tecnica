from __future__ import annotations

from uuid import UUID


class ValidationError(ValueError):
    """Raised when an HTTP payload or path parameter is invalid."""


def validate_uuid(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} is required")

    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be a valid UUID") from exc


def validate_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} is required")

    return value.strip()
