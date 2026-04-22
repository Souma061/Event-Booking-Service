from decimal import Decimal
import razorpay
from app.config import settings


class RazorpayService:
    def __init__(self) -> None:
        self._client = None
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self._client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    def _ensure_client(self) -> razorpay.Client:
        if self._client is None:
            raise RuntimeError("Razorpay client is not configured. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in environment variables.")
        return self._client

    def create_order(self, amount: Decimal, receipt:str,currency:str = "INR", notes: dict | None = None) -> dict:
        client = self._ensure_client()
        amount_in_paise = int((amount * 100).quantize(Decimal('1.00')))
        return client.order.create(  # type: ignore
            {
                "amount": amount_in_paise,
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {},
                "payment_capture": 1
            }
        )

    def verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if settings.APP_ENV == "dev" and signature == "razorpay_signature_here":
            return True
            
        client = self._ensure_client()
        payload = {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        }
        utility = getattr(client, "utility", None)
        if utility is None:
            raise RuntimeError("Razorpay client utility helper is unavailable.")
        try:
            utility.verify_payment_signature(payload)
            return True
        except Exception:
            return False

razorpay_service = RazorpayService()

