class PersistenceError(RuntimeError):
    """Raised when persistence fails without exposing driver internals."""


class DocumentNotFoundError(PersistenceError):
    """Raised when a document does not exist."""


class InvalidReferenceError(PersistenceError):
    """Raised when a request references a missing related record."""


class StorageError(RuntimeError):
    """Raised when object storage operations fail."""


class ComplianceGatewayError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class WebhookError(RuntimeError):
    """Raised when the BFF webhook cannot be called."""
