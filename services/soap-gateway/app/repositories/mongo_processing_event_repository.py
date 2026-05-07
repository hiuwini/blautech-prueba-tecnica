from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import GatewayConfig
from app.core.errors import PersistenceError


class MongoProcessingEventRepository:
    def __init__(self, config: GatewayConfig) -> None:
        from pymongo import MongoClient

        self.client = MongoClient(config.mongo_uri, serverSelectionTimeoutMS=2000)
        self.database = self.client[config.mongo_database]
        self.collection = self.database["processing_events"]

    def insert_event(
        self,
        *,
        document_id: str,
        status: str,
        message: str,
        created_at: datetime,
        check_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            self.collection.insert_one(
                {
                    "document_id": document_id,
                    "check_id": check_id,
                    "status": status,
                    "message": message,
                    "metadata": metadata or {},
                    "created_at": created_at,
                }
            )
        except Exception as exc:
            raise PersistenceError("Unable to persist processing event") from exc
