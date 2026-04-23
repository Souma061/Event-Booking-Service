import json
import urllib.request
import urllib.error
from app.config import settings

class CashfreeService:
    def __init__(self):
        self.app_id = settings.CASHFREE_APP_ID
        self.secret_key = settings.CASHFREE_SECRET_KEY
        if settings.CASHFREE_ENVIRONMENT == "PROD":
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

    def create_order(self, order_id: str, amount: float, currency: str, customer_id: str, customer_email: str, customer_phone: str):
        url = f"{self.base_url}/orders"
        payload = {
            "order_id": order_id,
            "order_amount": round(float(amount), 2),
            "order_currency": currency,
            "customer_details": {
                "customer_id": customer_id,
                "customer_email": customer_email if customer_email else "unknown@example.com",
                "customer_phone": customer_phone if customer_phone else "9999999999"
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"Cashfree API Error: {e.code} - {error_body}")
            raise RuntimeError(f"Cashfree API Error: {error_body}")

    def get_order(self, order_id: str):
        url = f"{self.base_url}/orders/{order_id}"
        req = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"Cashfree API Error: {error_body}")

cashfree_service = CashfreeService()
