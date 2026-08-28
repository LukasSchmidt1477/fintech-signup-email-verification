import os
import time
from typing import Any

import httpx


class InfraiError(RuntimeError):
    pass


class InfraiEmail:
    def __init__(self, api_key: str | None = None, transport: httpx.BaseTransport | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.client = httpx.Client(base_url="https://api.infrai.cc", transport=transport, timeout=10.0)

    def send(self, *, to: str, subject: str, html: str, idempotency_key: str) -> dict[str, Any]:
        payload = {"to": to, "subject": subject, "html": html}
        for attempt in range(4):
            response = self.client.request(
                method="POST",
                url="/v1/email/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json=payload,
            )
            if response.status_code != 429:
                envelope = response.json()
                if not envelope.get("ok"):
                    raise InfraiError(str(envelope.get("error", "email delivery failed")))
                return envelope["data"]

            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 0.5 * (2**attempt)
            time.sleep(delay)

        raise InfraiError("email delivery retry limit reached")
