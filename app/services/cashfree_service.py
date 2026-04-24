import json
import base64
import hashlib
import hmac
import time
import urllib.request
import urllib.error
from decimal import Decimal
from typing import Any

from app.config import settings


def _money_amount(value: Decimal | int | str) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01")))


class CashfreeService:
    def __init__(self):
        self.app_id = settings.CASHFREE_APP_ID
        self.secret_key = settings.CASHFREE_SECRET_KEY
        if settings.CASHFREE_ENVIRONMENT.upper() == "PROD":
            self.base_url = "https://api.cashfree.com/pg"
        else:
            self.base_url = "https://sandbox.cashfree.com/pg"
        
        self.headers = {
            "x-client-id": self.app_id,
            "x-client-secret": self.secret_key,
            "x-api-version": "2023-08-01",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_order(
        self,
        order_id: str,
        amount: Decimal | int | str,
        currency: str,
        customer_id: str,
        customer_email: str,
        customer_phone: str,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/orders"
        payload = {
            "order_id": order_id,
            "order_amount": _money_amount(amount),
            "order_currency": currency,
            "customer_details": {
                "customer_id": customer_id,
                "customer_email": customer_email if customer_email else "unknown@example.com",
                "customer_phone": customer_phone if customer_phone else "9999999999"
            }
        }
        if settings.CASHFREE_WEBHOOK_URL:
            payload["order_meta"] = {"notify_url": settings.CASHFREE_WEBHOOK_URL}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"Cashfree API Error: {e.code} - {error_body}")
            raise RuntimeError(f"Cashfree API Error: {error_body}")

    def get_order(self, order_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/orders/{order_id}"
        req = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"Cashfree API Error: {error_body}")

    def verify_webhook_signature(self, raw_body: bytes, signature: str | None, timestamp: str | None) -> bool:
        if not signature or not timestamp or not self.secret_key:
            return False

        try:
            timestamp_ms = int(timestamp)
        except ValueError:
            return False

        now_ms = int(time.time() * 1000)
        tolerance_ms = settings.CASHFREE_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS * 1000
        if abs(now_ms - timestamp_ms) > tolerance_ms:
            return False

        signed_payload = timestamp.encode("utf-8") + raw_body
        digest = hmac.new(
            self.secret_key.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).digest()
        expected_signature = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected_signature, signature)

cashfree_service = CashfreeService()
