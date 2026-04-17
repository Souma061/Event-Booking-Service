from __future__ import annotations
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import BookingStatus, PaymentStatus, TicketStatus


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_user_id_idempotency"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False, index=True)
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id"),nullable=False, index=True)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus),default=BookingStatus.PENDING_PAYMENT, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="bookings")
    show = relationship("Show", back_populates="bookings")
    items = relationship("BookingItem", back_populates="booking", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="booking" )
    tickets = relationship("Ticket", back_populates="booking")


class BookingItem(Base):
    __tablename__ = "booking_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price : Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    line_total : Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)

    booking = relationship("Booking", back_populates="items")



class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("provider_order_id",name="uq_provider_order_id"),)


    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id : Mapped[int] = mapped_column(ForeignKey("bookings.id"),index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50),default="RAZORPAY", nullable=False)
    provider_order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.CREATED, nullable=False)
    raw_upload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    booking = relationship("Booking", back_populates="payments")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"),nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False, index=True)
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id"),
                                                nullable=False, index=True)
    ticket_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    qr_payload: Mapped[str] = mapped_column(String(255), nullable=False)
    qr_image_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    status:Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.ACTIVE, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    booking = relationship("Booking", back_populates="tickets")
    show = relationship("Show", back_populates="tickets")


class NotificationLog(Base):
    __tablename__ = "notification_logs"


    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    details: Mapped[str | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
