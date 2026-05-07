from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import DocumentProcessingConfig
from app.core.errors import DocumentNotFoundError, InvalidReferenceError, PersistenceError
from app.domain.compliance.models import ComplianceSummary
from app.domain.documents.models import DocumentRecord


class PostgresDocumentRepository:
    def __init__(self, config: DocumentProcessingConfig) -> None:
        self.config = config

    def create_document(
        self,
        *,
        document_id: str,
        user_id: str | None,
        document_type: str,
        original_filename: str,
        content_type: str,
        size_bytes: int,
        bucket_name: str,
        object_key: str,
    ) -> DocumentRecord:
        import psycopg
        from psycopg.rows import dict_row

        try:
            with self._connect(row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO documents (
                          id,
                          user_id,
                          document_type,
                          original_filename,
                          content_type,
                          size_bytes,
                          bucket_name,
                          object_key,
                          status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'UPLOADED')
                        RETURNING
                          id::text AS document_id,
                          user_id::text AS user_id,
                          document_type,
                          original_filename,
                          content_type,
                          size_bytes,
                          bucket_name,
                          object_key,
                          status,
                          created_at,
                          updated_at,
                          processed_at
                        """,
                        (
                            document_id,
                            user_id,
                            document_type,
                            original_filename,
                            content_type,
                            size_bytes,
                            bucket_name,
                            object_key,
                        ),
                    )
                    row = cursor.fetchone()
        except psycopg.errors.ForeignKeyViolation as exc:
            raise InvalidReferenceError("Referenced user does not exist") from exc
        except Exception as exc:
            raise PersistenceError("Unable to create document metadata") from exc

        return _row_to_document(row)

    def list_documents(self, *, limit: int, offset: int) -> tuple[list[DocumentRecord], int]:
        from psycopg.rows import dict_row

        try:
            with self._connect(row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS total FROM documents")
                    total = int(cursor.fetchone()["total"])
                    cursor.execute(
                        """
                        SELECT
                          id::text AS document_id,
                          user_id::text AS user_id,
                          document_type,
                          original_filename,
                          content_type,
                          size_bytes,
                          bucket_name,
                          object_key,
                          status,
                          created_at,
                          updated_at,
                          processed_at
                        FROM documents
                        ORDER BY created_at DESC, id DESC
                        LIMIT %s OFFSET %s
                        """,
                        (limit, offset),
                    )
                    rows = cursor.fetchall()
        except Exception as exc:
            raise PersistenceError("Unable to list documents") from exc

        return [_row_to_document(row) for row in rows], total

    def get_document(self, document_id: str) -> DocumentRecord | None:
        from psycopg.rows import dict_row

        try:
            with self._connect(row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                          id::text AS document_id,
                          user_id::text AS user_id,
                          document_type,
                          original_filename,
                          content_type,
                          size_bytes,
                          bucket_name,
                          object_key,
                          status,
                          created_at,
                          updated_at,
                          processed_at
                        FROM documents
                        WHERE id = %s
                        """,
                        (document_id,),
                    )
                    row = cursor.fetchone()
        except Exception as exc:
            raise PersistenceError("Unable to read document") from exc

        return _row_to_document(row) if row else None

    def update_status(
        self,
        *,
        document_id: str,
        status: str,
        processed_at: datetime | None,
    ) -> DocumentRecord:
        from psycopg.rows import dict_row

        try:
            with self._connect(row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE documents
                        SET status = %s, processed_at = %s
                        WHERE id = %s
                        RETURNING
                          id::text AS document_id,
                          user_id::text AS user_id,
                          document_type,
                          original_filename,
                          content_type,
                          size_bytes,
                          bucket_name,
                          object_key,
                          status,
                          created_at,
                          updated_at,
                          processed_at
                        """,
                        (status, processed_at, document_id),
                    )
                    row = cursor.fetchone()
        except Exception as exc:
            raise PersistenceError("Unable to update document status") from exc

        if row is None:
            raise DocumentNotFoundError("Document does not exist")

        return _row_to_document(row)

    def get_latest_compliance(self, document_id: str) -> ComplianceSummary | None:
        from psycopg.rows import dict_row

        try:
            with self._connect(row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                          document_id::text AS document_id,
                          status,
                          check_id::text AS check_id,
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

        return _row_to_compliance(row) if row else None

    def _connect(self, *, row_factory: Any | None = None) -> Any:
        import psycopg

        kwargs: dict[str, Any] = {
            "host": self.config.postgres_host,
            "port": self.config.postgres_port,
            "dbname": self.config.postgres_db,
            "user": self.config.postgres_user,
            "password": self.config.postgres_password,
        }
        if row_factory is not None:
            kwargs["row_factory"] = row_factory

        return psycopg.connect(**kwargs)


def _row_to_document(row: Any) -> DocumentRecord:
    return DocumentRecord(
        document_id=row["document_id"],
        user_id=row["user_id"],
        document_type=row["document_type"],
        original_filename=row["original_filename"],
        content_type=row["content_type"],
        size_bytes=row["size_bytes"],
        bucket_name=row["bucket_name"],
        object_key=row["object_key"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        processed_at=row["processed_at"],
    )


def _row_to_compliance(row: Any) -> ComplianceSummary:
    return ComplianceSummary(
        document_id=row["document_id"],
        status=row["status"],
        check_id=row["check_id"],
        details=row["details"],
        checked_at=row["checked_at"],
    )
