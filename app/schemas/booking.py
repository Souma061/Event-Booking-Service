from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class BookingItemIn(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    quantity: int = Field(ge=1, le=100)


class BookingCreateRequest(BaseModel):
    show_id: int
    items:list[BookingItemIn] = Field(min_length=1)


class BookingItemOut(BaseModel):
    category: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)

class BookingOut(BaseModel):
    id: int
    user_id: int
    show_id: int
    status: str
    total_amount: Decimal
    currency: str
    created_at: datetime
    items: list[BookingItemOut]

    model_config = ConfigDict(from_attributes=True)
