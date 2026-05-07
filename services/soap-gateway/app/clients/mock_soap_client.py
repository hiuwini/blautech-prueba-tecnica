from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.errors import UpstreamSoapError


@dataclass(frozen=True)
class SoapHttpResponse:
    status_code: int
    body: str


class MockSoapClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def check_compliance(self, xml_body: str) -> SoapHttpResponse:
        request = Request(
            f"{self.base_url}/soap/compliance",
            data=xml_body.encode("utf-8"),
            headers={
                "Accept": "text/xml",
                "Content-Type": "text/xml; charset=utf-8",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                return SoapHttpResponse(status_code=response.status, body=body)
        except HTTPError as exc:
            try:
                body = exc.read().decode("utf-8")
            finally:
                exc.close()
            return SoapHttpResponse(status_code=exc.code, body=body)
        except URLError as exc:
            raise UpstreamSoapError("Mock SOAP Server is unavailable") from exc
