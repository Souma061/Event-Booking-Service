import hashlib
import json
import asyncio
from decimal import Decimal

from fastapi import APIRouter, Depends,HTTPException,Header,Request,status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from app.database import get_db, SessionLocal
from app.dependencies.auth import get_current_active_user
from app.models.booking import Booking,BookingItem
from app.models.event import Show,SeatCategoryInventory
from app.models.user import User
from app.models.enums import BookingStatus
from app.schemas.event import InventoryRowOut, ShowAvailabilityOut
from app.schemas.booking import BookingCreateRequest,BookingOut
from app.utils.rate_limit import booking_buckets, get_rate_limit_client_ip, rate_limit_headers


router  = APIRouter(prefix="/api/bookings",tags=["bookings"])

async def expire_unpaid_booking(booking_id: int):
    await asyncio.sleep(15 * 60)
    db = SessionLocal()
    try:
        booking = db.get(Booking, booking_id)
        if booking and booking.status == BookingStatus.PENDING_PAYMENT:
            for item in booking.items:
                inventory = db.execute(
                    select(SeatCategoryInventory)
                    .where(
                        SeatCategoryInventory.show_id == booking.show_id,
                        SeatCategoryInventory.category == item.category
                    )
                    .with_for_update()
                ).scalar_one_or_none()
                if inventory:
                    inventory.available_seats += item.quantity
            booking.status = BookingStatus.CANCELLED
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error expiring booking {booking_id}: {e}")
    finally:
        db.close()

@router.get("/shows/{show_id}/availability",response_model=ShowAvailabilityOut)
def show_availability(show_id:int, db: Session = Depends(get_db)):
    show = db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Show not found")

    rows = db.execute(
        select(SeatCategoryInventory)
        .where(SeatCategoryInventory.show_id == show_id)
        .order_by(SeatCategoryInventory.category.asc())
    ).scalars().all()

    return ShowAvailabilityOut(
        show_id=show.id,inventory=[InventoryRowOut.model_validate(row) for row in rows]
    )


@router.post("",response_model=BookingOut,status_code=status.HTTP_201_CREATED)
def create_booking(
    request:Request,
    payload: BookingCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    idempotency_key: str | None = Header(default=None,
                                         alias="Idempotency-Key")
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Idempotency-Key header is required")

    show = db.get(Show, payload.show_id)
    if not show or show.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Show not found or not active")

    payload_hash = hashlib.sha256(
        json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode("utf-8")
    ).hexdigest()

    existing = db.execute(
        select(Booking).where(
            Booking.user_id == current_user.id,
            Booking.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()

    if existing:
        if existing.request_hash != payload_hash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency-Key conflict")
        return existing

    rate_limit_key = f"{get_rate_limit_client_ip(request)}:{current_user.id}"
    bucket = booking_buckets[rate_limit_key]
    if not bucket.allow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many booking attempts. Please try again later.",
            headers=rate_limit_headers(bucket),
        )

    sorted_items = sorted(payload.items, key=lambda x: x.category)
    total_amount = Decimal("0.00")
    booking_items = []

    try:
        for item in sorted_items:
            inventory = db.execute(
                select(SeatCategoryInventory)
                .where(
                    SeatCategoryInventory.show_id == payload.show_id,
                    SeatCategoryInventory.category == item.category,
                )
                .with_for_update()
            ).scalar_one_or_none()

            if not inventory:
                raise HTTPException(
                    status_code = status.HTTP_400_BAD_REQUEST,
                    detail=f"Category '{item.category}' not found for this show"
                )
            if inventory.available_seats < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough seats available in category '{item.category}'"
                )
            inventory.available_seats -= item.quantity
            line_total = inventory.price * item.quantity
            total_amount += line_total
            booking_items.append(
                {
                    "category": item.category,
                    "quantity": item.quantity,
                    "unit_price": inventory.price,
                    "line_total": line_total
                }
            )
        booking = Booking(
            user_id = current_user.id,
            show_id = payload.show_id,
            status = BookingStatus.PENDING_PAYMENT,
            total_amount = total_amount,
            idempotency_key = idempotency_key,
            currency = "INR",
            request_hash = payload_hash,
        )
        db.add(booking)
        db.flush()
        for row in booking_items:
            db.add(
                BookingItem(booking_id= booking.id, **row))
        db.commit()
        db.refresh(booking)
        
        background_tasks.add_task(expire_unpaid_booking, booking.id)
        
        return booking
    except OperationalError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A concurrent transaction modified the seats. Please try again."
        )
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key conflict")
        existing = db.execute(
            select(Booking).where(
                Booking.user_id == current_user.id,
                Booking.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking creation failed due to a conflict. Please retry with the same Idempotency-Key or use a new one.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the booking. Please try again later.")

@router.get("/mine",response_model=list[BookingOut])
def my_bookings(
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)

):
    return db.execute(
        select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.created_at.desc())
    ).scalars().all()
