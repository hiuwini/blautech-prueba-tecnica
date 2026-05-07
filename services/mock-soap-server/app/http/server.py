from __future__ import annotations

from http.server import ThreadingHTTPServer

from app.config import DEFAULT_PORT
from app.http.handler import MockSoapHandler


def create_server(host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), MockSoapHandler)
