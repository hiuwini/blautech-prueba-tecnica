from __future__ import annotations

from datetime import timedelta
from io import BytesIO
from urllib.parse import urlparse

from app.core.config import DocumentProcessingConfig
from app.core.errors import StorageError


class MinioDocumentStorage:
    def __init__(self, config: DocumentProcessingConfig) -> None:
        from minio import Minio

        endpoint, secure = _normalize_endpoint(config.minio_endpoint, config.minio_secure)
        self.client = Minio(
            endpoint,
            access_key=config.minio_access_key,
            secret_key=config.minio_secret_key,
            secure=secure,
            region=config.minio_region,
        )
        self.presign_client = self.client
        if config.minio_public_endpoint:
            public_endpoint, public_secure = _normalize_endpoint(
                config.minio_public_endpoint,
                config.minio_secure,
            )
            self.presign_client = Minio(
                public_endpoint,
                access_key=config.minio_access_key,
                secret_key=config.minio_secret_key,
                secure=public_secure,
                region=config.minio_region,
            )

    def put_document(
        self,
        *,
        bucket_name: str,
        object_key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        try:
            self.client.put_object(
                bucket_name,
                object_key,
                BytesIO(content),
                length=len(content),
                content_type=content_type,
            )
        except Exception as exc:
            raise StorageError("Unable to store document object") from exc

    def presigned_download_url(
        self,
        *,
        bucket_name: str,
        object_key: str,
        expires_in_seconds: int,
    ) -> str:
        try:
            return self.presign_client.presigned_get_object(
                bucket_name,
                object_key,
                expires=timedelta(seconds=expires_in_seconds),
            )
        except Exception as exc:
            raise StorageError("Unable to create presigned download URL") from exc


def _normalize_endpoint(raw_endpoint: str, default_secure: bool) -> tuple[str, bool]:
    parsed = urlparse(raw_endpoint)
    if parsed.scheme in {"http", "https"}:
        endpoint = parsed.netloc
        if parsed.path and parsed.path != "/":
            endpoint = f"{endpoint}{parsed.path}"
        return endpoint, parsed.scheme == "https"

    return raw_endpoint, default_secure
