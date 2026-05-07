from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.config import GatewayConfig
from app.core.errors import DocumentNotFoundError, PersistenceError


@dataclass(frozen=True)
class ComplianceRecord:
    document_id: str
    check_id: str
    status: str
    details: str
    checked_at: datetime
    raw_request_xml: str
    raw_response_xml: str


class PostgresComplianceRepository:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config

    def save_check(self, record: ComplianceRecord) -> None:
        import psycopg

        try:
            with psycopg.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                dbname=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO compliance_checks (
                          document_id,
                          check_id,
                          status,
                          details,
                          checked_at,
                          raw_request_xml,
                          raw_response_xml
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            record.document_id,
                            record.check_id,
                            record.status,
                            record.details,
                            record.checked_at,
                            record.raw_request_xml,
                            record.raw_response_xml,
                        ),
                    )
        except psycopg.errors.ForeignKeyViolation as exc:
            raise DocumentNotFoundError("Document does not exist") from exc
        except Exception as exc:
            raise PersistenceError("Unable to persist compliance check") from exc

    def get_latest_by_document_id(self, document_id: str) -> dict[str, Any] | None:
        import psycopg
        from psycopg.rows import dict_row

        try:
            with psycopg.connect(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                dbname=self.config.postgres_db,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                row_factory=dict_row,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                          document_id::text AS document_id,
                          check_id::text AS check_id,
                          status,
                          details,
                          checked_at
                        FROM compliance_checks
                        WHERE document_id = %s
                        ORDER BY checked_at DESC, created_at DESC
                        LIMIT 1
                        """,
                        (document_id,),
                    )
                    row = cursor.fetchone()
        except Exception as exc:
            raise PersistenceError("Unable to read compliance status") from exc

        return dict(row) if row else None
