from pydantic import BaseModel, Field

class PaymentOrderCreateRequest(BaseModel):
    booking_id: int

class PaymentOrderOut(BaseModel):
    booking_id: int
    provider_order_id: str
    amount_in_paise: int
    currency: str
    payment_session_id: str


class PaymentVerificationRequest(BaseModel):
    booking_id: int
    provider_order_id: str


class PaymentVerificationOut(BaseModel):
    booking_id: int
    status: str
    ticket_codes: list[str] = Field(default_factory=list)
    
