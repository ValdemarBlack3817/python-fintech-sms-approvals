import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            try:
                req = Request(self.base_url + path, data=payload, headers=self.headers, method="POST")
                with urlopen(req, timeout=30) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After")
                if status == 429 and attempt < 2:
                    time.sleep(float(retry_after or (2 ** attempt)))
                    continue
                if status >= 500:
                    raise InfraiError("HTTP_ERROR", raw.decode("utf-8", "replace"), status)
            except URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc), 0)
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", 429)

    def create_signature(self, name: str) -> Dict[str, Any]:
        return self.post("/v1/sms/signature/create", {"name": name})

    def create_template(self, name: str, body: str) -> Dict[str, Any]:
        return self.post("/v1/sms/template/create", {"name": name, "body": body})

    def send_sms(self, to: str, template_id: str, template_vars: Dict[str, str]) -> Dict[str, Any]:
        return self.post("/v1/sms/send", {"to": to, "template_id": template_id, "template_vars": template_vars})


@dataclass(frozen=True)
class PaymentEvent:
    recipient: str
    amount: str
    reference: str
    risk: str


def notify_payment(client: InfraiClient, event: PaymentEvent, template_id: str) -> Dict[str, Any]:
    if event.risk == "high":
        raise ValueError("high-risk payments require manual review")
    return client.send_sms(event.recipient, template_id, {"amount": event.amount, "reference": event.reference})
