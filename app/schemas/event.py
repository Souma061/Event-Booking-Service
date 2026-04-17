import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class VenueCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=255)
    address: str = Field(min_length=5, max_length=255)


class VenueOut(BaseModel):
    id: int
    name: str
    city: str
    address: str

    model_config = ConfigDict(from_attributes=True)

class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    category: str = Field(min_length=2, max_length=100)
    venue_id: int

class EventOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    venue_id: int
    created_by_user_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class ShowCreate(BaseModel):
    start_at: datetime.datetime
    end_at: datetime.datetime
    status: str = Field(default="ACTIVE", max_length=30)

class ShowOut(BaseModel):
    id: int
    event_id: int
    start_at: datetime.datetime
    end_at: datetime.datetime
    status: str

    model_config = ConfigDict(from_attributes=True)

class InventoryRowIn(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    price: Decimal = Field(gt=0)
    total_seats: int = Field(ge=1,le=50000)


class InventoryRowOut(BaseModel):
    id: int
    show_id: int
    category: str
    price: Decimal
    total_seats: int
    available_seats: int

    model_config = ConfigDict(from_attributes=True)

class ShowAvailabilityOut(BaseModel):
    show_id: int
    inventory: list[InventoryRowOut]
