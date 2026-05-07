class SoapParseError(ValueError):
    """Raised when a SOAP response cannot be parsed as a compliance result."""


class SoapFaultError(ValueError):
    def __init__(self, fault_code: str, fault_string: str) -> None:
        super().__init__(fault_string)
        self.fault_code = fault_code
        self.fault_string = fault_string

    @property
    def is_client_fault(self) -> bool:
        return self.fault_code.endswith(":Client") or self.fault_code == "Client"
