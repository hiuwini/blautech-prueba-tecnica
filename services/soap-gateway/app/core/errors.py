class PersistenceError(RuntimeError):
    """Raised when persistence fails without exposing driver internals."""


class DocumentNotFoundError(PersistenceError):
    """Raised when compliance references a document missing in PostgreSQL."""


class UpstreamSoapError(RuntimeError):
    """Raised when the Mock SOAP Server cannot be reached."""
