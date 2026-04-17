from pydantic import BaseModel, Field

class PaymentOrderCreateRequest(BaseModel):
    booking_id: int

class PaymentOrderOut(BaseModel):
    booking_id: int
    provider_order_id: str
    amount_in_paise: int
    currency: str
    razorpay_key_id: str


class PaymentVerificationRequest(BaseModel):
    booking_id: int
    provider_order_id: str
    provider_payment_id: str
    provider_signature: str

class PaymentVerificationOut(BaseModel):
    booking_id: int
    status: str
    ticket_codes: list[str] = Field(default_factory=list)
    
