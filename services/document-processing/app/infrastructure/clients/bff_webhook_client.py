from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.errors import WebhookError


class BffWebhookClient:
    def __init__(self, *, webhook_url: str | None, timeout_seconds: float) -> None:
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return self.webhook_url is not None

    def notify_processing_complete(self, payload: dict[str, Any]) -> bool | None:
        if self.webhook_url is None:
            return None

        request = Request(
            self.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return 200 <= response.status < 300
        except HTTPError as exc:
            try:
                exc.read()
            finally:
                exc.close()
            raise WebhookError("BFF webhook returned an error") from exc
        except URLError as exc:
            raise WebhookError("BFF webhook is unavailable") from exc
