from fastapi.testclient import TestClient
from app.main import app
from app.utils.security import create_access_token
import json

client = TestClient(app)
user_id = "2"
token = create_access_token(user_id)
headers = {"Authorization": f"Bearer {token}"}

print("1. Requesting Payment Order...")
response = client.post(
    "/api/payments/orders",
    headers=headers,
    json={"booking_id": 4}
)
resp_json = response.json()
print("Order Response:", json.dumps(resp_json, indent=2))

order_id = resp_json.get("provider_order_id")
if not order_id:
    print("FAILED TO CREATE ORDER")
    exit(1)

print("\n2. Verifying Payment with dummy signature...")
verify_response = client.post(
    "/api/payments/verify",
    headers=headers,
    json={
        "booking_id": 4,
        "provider_order_id": order_id,
        "provider_payment_id": "razorpay_payment_id_here",
        "provider_signature": "razorpay_signature_here"
    }
)

print("Verify Response:", json.dumps(verify_response.json(), indent=2))
