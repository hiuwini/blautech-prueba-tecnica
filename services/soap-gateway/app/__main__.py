from __future__ import annotations

from app import create_app
from app.core.config import GatewayConfig


def main() -> None:
    config = GatewayConfig.from_env()
    app = create_app(config=config)
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    main()
