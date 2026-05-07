from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class GatewayConfig:
    host: str
    port: int
    mock_soap_base_url: str
    mock_soap_timeout_seconds: float
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    mongo_uri: str
    mongo_database: str
    service_name: str = "soap-gateway"

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        return cls(
            host=os.getenv("SOAP_GATEWAY_HOST", "0.0.0.0"),
            port=_get_int("SOAP_GATEWAY_PORT", 8001),
            mock_soap_base_url=os.getenv(
                "MOCK_SOAP_BASE_URL",
                "http://mock-soap-server:8090",
            ),
            mock_soap_timeout_seconds=_get_float("MOCK_SOAP_TIMEOUT_SECONDS", 5.0),
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
        )


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)
