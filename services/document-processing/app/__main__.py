from __future__ import annotations

import uvicorn

from app import create_app
from app.core.config import DocumentProcessingConfig


def main() -> None:
    config = DocumentProcessingConfig.from_env()
    uvicorn.run(
        create_app(config),
        host=config.host,
        port=config.port,
    )


if __name__ == "__main__":
    main()
