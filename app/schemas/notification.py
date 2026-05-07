from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class NotificationEventType(str, Enum):
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_EXPIRED = "booking_expired"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    TICKET_ISSUED = "ticket_issued"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class NotificationChannel(str, Enum):
    WEBSOCKET = "websocket"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class NotificationEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: NotificationEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int
    booking_id: int | None = None
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    channels: list[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.WEBSOCKET]
    )
    priority: NotificationPriority = NotificationPriority.NORMAL


class NotificationDelivery(BaseModel):
    channel: NotificationChannel
    status: str
    error_message: str | None = None
    retry_count: int = 0
