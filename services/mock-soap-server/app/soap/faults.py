class SoapRequestError(ValueError):
    """Raised when a SOAP request cannot be parsed into a compliance check."""


class SoapFaultError(ValueError):
    """Raised when a parsed SOAP request maps to a SOAP Fault."""
