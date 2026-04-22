import razorpay
from decimal import Decimal

client = razorpay.Client(auth=("rzp_test_SgaZDbJhmtr57D", "eXNuNLbEnZoBc4ZLDWxNspIc"))
amount = Decimal("1299.00")
amount_in_paise = int((amount * 100).quantize(Decimal('1.00')))
try:
    print(client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": "receipt_123",
        "payment_capture": 1
    }))
except Exception as e:
    print(f"Error: {e}")
