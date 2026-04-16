from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint,func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base



class Venue(Base):
    __tablename__ = "venues"


    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    events = relationship("Event", back_populates="venue", cascade="all, delete-orphan")



class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text,nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),nullable=False)


    venue = relationship("Venue", back_populates="events")
    shows = relationship("Show", back_populates="event", cascade="all, delete-orphan")

class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"),nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)


    event = relationship("Event", back_populates="shows")
    inventories = relationship("SeatCategoryInventory",back_populates="show", cascade="all, delete-orphan")
    bookings = relationship("Booking",back_populates="show",
                            cascade="all, delete-orphan")

    tickets = relationship("Ticket", back_populates="show", cascade="all, delete-orphan")



class SeatCategoryInventory(Base):
    __tablename__ = "seat_category_inventory"
    __table_args__ = (UniqueConstraint("show_id","category",name="uq_show_category"),)

    id: Mapped[int] = mapped_column(primary_key=True )
    show_id: Mapped[int] = mapped_column(ForeignKey("shows.id"),index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50),nullable=False)
    total_seats: Mapped[int] = mapped_column(nullable=False)
    available_seats: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)

    show = relationship("Show", back_populates="inventories")



