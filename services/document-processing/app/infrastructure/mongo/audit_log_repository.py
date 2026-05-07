from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import DocumentProcessingConfig
from app.core.errors import PersistenceError


class MongoAuditLogRepository:
    def __init__(self, config: DocumentProcessingConfig) -> None:
        from pymongo import MongoClient

        self.client = MongoClient(config.mongo_uri, serverSelectionTimeoutMS=2000)
        self.database = self.client[config.mongo_database]
        self.collection = self.database["audit_logs"]

    def insert_document_uploaded(
        self,
        *,
        document_id: str,
        user_id: str | None,
        metadata: dict[str, Any],
        created_at: datetime,
    ) -> None:
        try:
            self.collection.insert_one(
                {
                    "action": "DOCUMENT_UPLOADED",
                    "entity_type": "document",
                    "entity_id": document_id,
                    "user_id": user_id,
                    "metadata": metadata,
                    "created_at": created_at,
                }
            )
        except Exception as exc:
            raise PersistenceError("Unable to persist audit log") from exc
