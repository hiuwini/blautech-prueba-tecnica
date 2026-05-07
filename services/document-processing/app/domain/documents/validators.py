from __future__ import annotations

import re
from pathlib import PurePath
from uuid import UUID


class ValidationError(ValueError):
    def __init__(self, field_name: str, message: str) -> None:
        super().__init__(message)
        self.field_name = field_name
        self.message = message


def validate_uuid(value: str, field_name: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ValidationError(field_name, f"{field_name} must be a valid UUID") from exc


def validate_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(field_name, f"{field_name} is required")
    return value.strip()


def sanitize_filename(filename: str | None) -> str:
    if filename is None:
        raise ValidationError("file", "file filename is required")

    base_name = PurePath(filename).name.strip()
    if not base_name:
        raise ValidationError("file", "file filename is required")

    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name)
    if not sanitized:
        raise ValidationError("file", "file filename is required")

    return sanitized[:255]
