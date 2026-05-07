from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Final


DEFAULT_PORT: Final = 8090
MAX_REQUEST_BYTES: Final = 1024 * 1024


@dataclass(frozen=True)
class MockSoapConfig:
    host: str
    port: int

    @classmethod
    def from_env(cls) -> "MockSoapConfig":
        return cls(
            host=os.getenv("MOCK_SOAP_HOST", "0.0.0.0"),
            port=int(os.getenv("MOCK_SOAP_PORT", str(DEFAULT_PORT))),
        )
