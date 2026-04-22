import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.booking import Booking, Payment, Ticket
from app.models.enums import BookingStatus, PaymentStatus
from app.models.user import User
from app.schemas.payment import (
    PaymentOrderCreateRequest,
    PaymentOrderOut,
    PaymentVerificationOut,
    PaymentVerificationRequest,
)
from app.services.email_services import send_booking_confirmation_email_sync
from app.services.payment_service import razorpay_service
from app.services.qr_services import build_ticket_payload, generate_qr_base64


router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/orders", response_model=PaymentOrderOut)
def create_payment_order(
    payload: PaymentOrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    booking = db.get(Booking, payload.booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != BookingStatus.PENDING_PAYMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment order can only be created for bookings pending payment",
        )

    existing_payment = db.execute(
        select(Payment)
        .where(Payment.booking_id == booking.id, Payment.status == PaymentStatus.CREATED)
        .order_by(Payment.id.desc())
    ).scalars().first()

    if existing_payment:
        amount_in_paise = int(booking.total_amount * 100)
        return PaymentOrderOut(
            booking_id=booking.id,
            provider_order_id=existing_payment.provider_order_id,
            amount_in_paise=amount_in_paise,
            currency=booking.currency,
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
        )

    try:
        order = razorpay_service.create_order(
            amount=booking.total_amount,
            receipt=f"booking_{booking.id}_{secrets.token_hex(8)}",
            currency=booking.currency,
            notes={"booking_id": str(booking.id), "user_id": str(current_user.id)},
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create payment order with Razorpay",
        )
    except Exception as e:
        print(f"DEBUG: Exception in Razorpay create_order: {repr(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error while creating order",
        )

    payment = Payment(
        booking_id=booking.id,
        provider="RAZORPAY",
        provider_order_id=order["id"],
        amount=booking.total_amount,
        currency=booking.currency,
        status=PaymentStatus.CREATED,
        raw_upload=order,
    )
    db.add(payment)
    db.commit()

    amount_in_paise = int(booking.total_amount * 100)
    return PaymentOrderOut(
        booking_id=booking.id,
        provider_order_id=order["id"],
        amount_in_paise=amount_in_paise,
        currency=booking.currency,
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/verify", response_model=PaymentVerificationOut)
def verify_payment(
    payload: PaymentVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    booking = db.get(Booking, payload.booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    payment = db.execute(
        select(Payment).where(
            Payment.booking_id == booking.id,
            Payment.provider_order_id == payload.provider_order_id,
        )
    ).scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    if payment.status == PaymentStatus.CAPTURED and booking.status == BookingStatus.CONFIRMED:
        codes = [ticket.ticket_code for ticket in booking.tickets]
        return PaymentVerificationOut(
            booking_id=booking.id,
            status=booking.status.value,
            ticket_codes=codes,
        )

    try:
        signature_ok = razorpay_service.verify_signature(
            order_id=payload.provider_order_id,
            payment_id=payload.provider_payment_id,
            signature=payload.provider_signature,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider is not configured",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error while verifying payment",
        )

    payment.provider_payment_id = payload.provider_payment_id
    payment.provider_signature = payload.provider_signature

    if not signature_ok:
        payment.status = PaymentStatus.FAILED
        booking.status = BookingStatus.FAILED
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature")

    payment.status = PaymentStatus.CAPTURED
    booking.status = BookingStatus.CONFIRMED

    existing_tickets = list(booking.tickets)
    if not existing_tickets:
        total_quantity = sum(item.quantity for item in booking.items)
        for _ in range(total_quantity):
            ticket_code = f"TKT-{booking.id}-{secrets.token_hex(4).upper()}"
            qr_payload_dict = build_ticket_payload(
                ticket_code=ticket_code,
                booking_id=booking.id,
                show_id=booking.show_id,
                user_id=current_user.id,
            )
            qr_image_base64, qr_payload = generate_qr_base64(qr_payload_dict)
            ticket = Ticket(
                booking_id=booking.id,
                user_id=current_user.id,
                show_id=booking.show_id,
                ticket_code=ticket_code,
                qr_payload=qr_payload,
                qr_image_base64=qr_image_base64,
            )
            db.add(ticket)
            existing_tickets.append(ticket)

    db.commit()

    ticket_codes = [ticket.ticket_code for ticket in existing_tickets]
    if current_user.email:
        background_tasks.add_task(
            send_booking_confirmation_email_sync,
            current_user.email,
            booking.id,
            ticket_codes,
        )

    return PaymentVerificationOut(
        booking_id=booking.id,
        status=booking.status.value,
        ticket_codes=ticket_codes,
    )
