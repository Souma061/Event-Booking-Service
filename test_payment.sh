#!/bin/bash
BOOKING_ID=${1:-4}
TOKEN=${TOKEN:-""}

# If token is not set, login as user 2 (assuming default pw)
if [ -z "$TOKEN" ]; then
    echo "Logging in to get token..."
    LOGIN_RESP=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"demo.user@example.com","password":"password123"}')
    TOKEN=$(echo "$LOGIN_RESP" | ./venv/bin/python -c "import sys,json; data=json.load(sys.stdin); print(data.get('access_token','')) if isinstance(data, dict) else print('')")
fi

echo "Requesting Payment Order JSON..."
ORDER_JSON=$(curl -s -X POST "http://localhost:8000/api/payments/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"booking_id\": $BOOKING_ID}")

echo "Response: $ORDER_JSON"

ORDER_ID=$(echo "$ORDER_JSON" | ./venv/bin/python -c "import sys,json; data=json.load(sys.stdin); print(data.get('provider_order_id','')) if isinstance(data, dict) else print('')")
echo "Extracted ORDER_ID: $ORDER_ID"

if [ -z "$ORDER_ID" ]; then
    echo "Failed to extract ORDER_ID. Exiting."
    exit 1
fi

echo "Verifying payment..."
VERIFY_JSON=$(curl -s -X POST "http://localhost:8000/api/payments/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"booking_id\": $BOOKING_ID,
    \"provider_order_id\": \"$ORDER_ID\",
    \"provider_payment_id\": \"razorpay_payment_id_here\",
    \"provider_signature\": \"razorpay_signature_here\"
  }")

echo "Verify Response: $VERIFY_JSON"
