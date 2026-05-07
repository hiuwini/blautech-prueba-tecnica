from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DocumentProcessingConfig:
    host: str
    port: int
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    mongo_uri: str
    mongo_database: str
    minio_endpoint: str
    minio_public_endpoint: str | None
    minio_bucket: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool
    minio_region: str
    soap_gateway_base_url: str
    soap_gateway_timeout_seconds: float
    bff_webhook_url: str | None
    bff_webhook_timeout_seconds: float
    cors_allowed_origins: tuple[str, ...]
    presigned_url_expiry_seconds: int
    service_name: str = "document-processing"

    @classmethod
    def from_env(cls) -> "DocumentProcessingConfig":
        return cls(
            host=os.getenv("DOCUMENT_PROCESSING_HOST", "0.0.0.0"),
            port=_get_int("DOCUMENT_PROCESSING_PORT", 8000),
            postgres_host=os.getenv("POSTGRES_HOST", "postgres"),
            postgres_port=_get_int("POSTGRES_PORT", 5432),
            postgres_db=os.getenv("POSTGRES_DB", "regulatory_platform"),
            postgres_user=os.getenv("POSTGRES_USER", "regulatory_user"),
            postgres_password=os.getenv(
                "POSTGRES_PASSWORD",
                "change_me_local_postgres_password",
            ),
            mongo_uri=os.getenv("MONGO_URI", "mongodb://mongo:27017/regulatory_audit"),
            mongo_database=os.getenv("MONGO_DATABASE", "regulatory_audit"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
            minio_public_endpoint=_optional_env("MINIO_PUBLIC_ENDPOINT"),
            minio_bucket=os.getenv("MINIO_BUCKET", "regulatory-documents"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "local_minio_user"),
            minio_secret_key=os.getenv(
                "MINIO_SECRET_KEY",
                "change_me_local_minio_password",
            ),
            minio_secure=_get_bool("MINIO_SECURE", False),
            minio_region=_optional_env("MINIO_REGION") or "us-east-1",
            soap_gateway_base_url=os.getenv(
                "SOAP_GATEWAY_BASE_URL",
                "http://soap-gateway:8001",
            ),
            soap_gateway_timeout_seconds=_get_float("SOAP_GATEWAY_TIMEOUT_SECONDS", 5.0),
            bff_webhook_url=_optional_env("BFF_WEBHOOK_URL"),
            bff_webhook_timeout_seconds=_get_float("BFF_WEBHOOK_TIMEOUT_SECONDS", 3.0),
            cors_allowed_origins=_get_csv(
                "DOCUMENT_PROCESSING_CORS_ALLOWED_ORIGINS",
                ("http://localhost:3000",),
            ),
            presigned_url_expiry_seconds=_get_int(
                "DOCUMENT_PROCESSING_PRESIGNED_URL_EXPIRY_SECONDS",
                900,
            ),
        )


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None or not value.strip() else int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None or not value.strip() else float(value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    items = tuple(item.strip() for item in value.split(",") if item.strip())
    return items or default
