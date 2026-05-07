from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    user_id: str | None
    document_type: str
    original_filename: str
    content_type: str
    size_bytes: int
    bucket_name: str
    object_key: str
    status: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
