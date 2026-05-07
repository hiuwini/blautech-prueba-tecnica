from __future__ import annotations

from app.config import MockSoapConfig
from app.http.server import create_server


def main() -> None:
    config = MockSoapConfig.from_env()
    server = create_server(host=config.host, port=config.port)
    print(f"Mock SOAP Server listening on {config.host}:{config.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
