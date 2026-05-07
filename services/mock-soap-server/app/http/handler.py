from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from app.config import MAX_REQUEST_BYTES
from app.soap import (
    SoapFaultError,
    SoapRequestError,
    build_compliance_response,
    build_fault,
    parse_compliance_request,
)


class MockSoapHandler(BaseHTTPRequestHandler):
    server_version = "MockSoapServer/1.0"

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send_json({"error": "Not Found"}, status=404)
            return

        self._send_json({"status": "ok", "service": "mock-soap-server"})

    def do_POST(self) -> None:
        if self.path != "/soap/compliance":
            self._send_soap(build_fault("Unknown SOAP endpoint"), status=404)
            return

        payload = self._read_request_body()
        if payload is None:
            return

        try:
            request = parse_compliance_request(payload)
            response_xml = build_compliance_response(request)
        except SoapRequestError as exc:
            self._send_soap(build_fault(str(exc)), status=400)
            return
        except SoapFaultError as exc:
            self._send_soap(build_fault(str(exc)), status=500)
            return

        self._send_soap(response_xml, status=200)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_request_body(self) -> bytes | None:
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            self._send_soap(build_fault("Content-Length is required"), status=411)
            return None

        try:
            length = int(content_length)
        except ValueError:
            self._send_soap(build_fault("Invalid Content-Length"), status=400)
            return None

        if length > MAX_REQUEST_BYTES:
            self._send_soap(build_fault("Request payload is too large"), status=413)
            return None

        return self.rfile.read(length)

    def _send_json(self, payload: dict[str, str], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _send_soap(self, xml_body: str, status: int = 200) -> None:
        body = xml_body.encode("utf-8")
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
