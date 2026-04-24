import json
import secrets
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.booking import Booking, Payment, Ticket
from app.models.enums import BookingStatus, PaymentStatus
from app.models.event import SeatCategoryInventory
from app.models.user import User
from app.schemas.payment import (
    PaymentOrderCreateRequest,
    PaymentOrderOut,
    PaymentVerificationOut,
    PaymentVerificationRequest,
)
from app.services.email_services import send_booking_confirmation_email_sync
from app.services.cashfree_service import cashfree_service
from app.services.qr_services import build_ticket_payload, generate_qr_base64


router = APIRouter(prefix="/api/payments", tags=["payments"])


PAID_ORDER_STATUS = "PAID"
FAILED_ORDER_STATUSES = {"FAILED", "CANCELLED", "EXPIRED", "TERMINATED"}
FAILED_PAYMENT_STATUSES = {"FAILED", "CANCELLED", "USER_DROPPED"}


def _decimal_money(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _cashfree_order_amount(cf_order: dict[str, Any]) -> Decimal | None:
    value = cf_order.get("order_amount")
    return _decimal_money(value) if value is not None else None


def _cashfree_order_currency(cf_order: dict[str, Any]) -> str | None:
    value = cf_order.get("order_currency")
    return str(value).upper() if value is not None else None


def _cashfree_event_order(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data")
    if not isinstance(data, dict):
        return {}

    order = data.get("order") or data.get("order_details")
    return order if isinstance(order, dict) else {}


def _cashfree_event_payment(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data")
    if not isinstance(data, dict):
        return {}

    payment = data.get("payment") or data.get("payment_details")
    return payment if isinstance(payment, dict) else {}


def _payment_ticket_codes(booking: Booking) -> list[str]:
    return [ticket.ticket_code for ticket in booking.tickets]


def _issue_tickets_if_needed(db: Session, booking: Booking) -> list[str]:
    existing_tickets = list(booking.tickets)
    if existing_tickets:
        return [ticket.ticket_code for ticket in existing_tickets]

    total_quantity = sum(item.quantity for item in booking.items)
    ticket_codes = []
    for _ in range(total_quantity):
        ticket_code = f"TKT-{booking.id}-{secrets.token_hex(4).upper()}"
        qr_payload_dict = build_ticket_payload(
            ticket_code=ticket_code,
            booking_id=booking.id,
            show_id=booking.show_id,
            user_id=booking.user_id,
        )
        qr_image_base64, qr_payload = generate_qr_base64(qr_payload_dict)
        ticket = Ticket(
            booking_id=booking.id,
            user_id=booking.user_id,
            show_id=booking.show_id,
            ticket_code=ticket_code,
            qr_payload=qr_payload,
            qr_image_base64=qr_image_base64,
        )
        db.add(ticket)
        ticket_codes.append(ticket_code)

    return ticket_codes


def _release_inventory_for_failed_booking(db: Session, booking: Booking) -> None:
    if booking.status != BookingStatus.PENDING_PAYMENT:
        return

    for item in booking.items:
        inventory = db.execute(
            select(SeatCategoryInventory)
            .where(
                SeatCategoryInventory.show_id == booking.show_id,
                SeatCategoryInventory.category == item.category,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if inventory:
            inventory.available_seats = min(
                inventory.total_seats,
                inventory.available_seats + item.quantity,
            )


def _confirm_cashfree_payment(
    db: Session,
    *,
    booking_id: int,
    provider_order_id: str,
    cf_order: dict[str, Any],
    provider_payment_id: str | None = None,
    raw_event: dict[str, Any] | None = None,
    terminal_failure: bool = False,
    raise_on_incomplete: bool = True,
) -> PaymentVerificationOut:
    payment = db.execute(
        select(Payment)
        .where(
            Payment.booking_id == booking_id,
            Payment.provider_order_id == provider_order_id,
            Payment.provider == "CASHFREE",
        )
        .with_for_update()
    ).scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    booking = db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if payment.status == PaymentStatus.CAPTURED and booking.status == BookingStatus.CONFIRMED:
        return PaymentVerificationOut(
            booking_id=booking.id,
            status=booking.status.value,
            ticket_codes=_payment_ticket_codes(booking),
        )

    if cf_order.get("order_id") != payment.provider_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment order mismatch")

    gateway_amount = _cashfree_order_amount(cf_order)
    if gateway_amount is None or gateway_amount != _decimal_money(booking.total_amount):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount mismatch")

    gateway_currency = _cashfree_order_currency(cf_order)
    if gateway_currency != booking.currency.upper():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment currency mismatch")

    order_status = str(cf_order.get("order_status") or "").upper()
    raw_upload = dict(payment.raw_upload or {})
    raw_upload["latest_order"] = cf_order
    if raw_event:
        raw_upload["latest_webhook"] = raw_event
    payment.raw_upload = raw_upload

    if order_status != PAID_ORDER_STATUS:
        if terminal_failure or order_status in FAILED_ORDER_STATUSES:
            _release_inventory_for_failed_booking(db, booking)
            payment.status = PaymentStatus.FAILED
            booking.status = BookingStatus.FAILED
            db.commit()
            if not raise_on_incomplete:
                return PaymentVerificationOut(
                    booking_id=booking.id,
                    status=booking.status.value,
                    ticket_codes=[],
                )
        if not raise_on_incomplete:
            db.commit()
            return PaymentVerificationOut(
                booking_id=booking.id,
                status=booking.status.value,
                ticket_codes=[],
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment not completed. Status: {order_status or 'UNKNOWN'}",
        )

    payment.status = PaymentStatus.CAPTURED
    payment.provider_payment_id = provider_payment_id or payment.provider_payment_id
    booking.status = BookingStatus.CONFIRMED
    ticket_codes = _issue_tickets_if_needed(db, booking)
    db.commit()

    return PaymentVerificationOut(
        booking_id=booking.id,
        status=booking.status.value,
        ticket_codes=ticket_codes,
    )


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

    if existing_payment and existing_payment.raw_upload:
        try:
            session_id = existing_payment.raw_upload.get("payment_session_id")
            if session_id:
                amount_in_paise = int(booking.total_amount * 100)
                return PaymentOrderOut(
                    booking_id=booking.id,
                    provider_order_id=existing_payment.provider_order_id,
                    amount_in_paise=amount_in_paise,
                    currency=booking.currency,
                    payment_session_id=session_id,
                )
        except Exception:
            pass

    order_id = f"order_{booking.id}_{secrets.token_hex(4)}"

    try:
        cf_order = cashfree_service.create_order(
            order_id=order_id,
            amount=booking.total_amount,
            currency=booking.currency,
            customer_id=f"cust_{current_user.id}",
            customer_email=current_user.email,
            customer_phone=current_user.phone
        )
    except Exception as e:
        print(f"DEBUG: Exception in Cashfree create_order: {repr(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error while creating order",
        )

    payment = Payment(
        booking_id=booking.id,
        provider="CASHFREE",
        provider_order_id=cf_order["order_id"],
        amount=booking.total_amount,
        currency=booking.currency,
        status=PaymentStatus.CREATED,
        raw_upload=cf_order,
    )
    db.add(payment)
    db.commit()

    amount_in_paise = int(booking.total_amount * 100)
    return PaymentOrderOut(
        booking_id=booking.id,
        provider_order_id=cf_order["order_id"],
        amount_in_paise=amount_in_paise,
        currency=booking.currency,
        payment_session_id=cf_order["payment_session_id"],
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

    try:
        cf_order = cashfree_service.get_order(order_id=payload.provider_order_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error while verifying payment",
        )

    was_already_captured = payment.status == PaymentStatus.CAPTURED
    result = _confirm_cashfree_payment(
        db,
        booking_id=booking.id,
        provider_order_id=payload.provider_order_id,
        cf_order=cf_order,
    )
    if current_user.email and result.ticket_codes and not was_already_captured:
        background_tasks.add_task(
            send_booking_confirmation_email_sync,
            current_user.email,
            booking.id,
            result.ticket_codes,
        )

    return result


@router.post("/cashfree/webhook")
async def cashfree_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    signature = request.headers.get("x-webhook-signature")
    timestamp = request.headers.get("x-webhook-timestamp")

    if not cashfree_service.verify_webhook_signature(raw_body, signature, timestamp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    try:
        event = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload")

    order = _cashfree_event_order(event)
    payment_data = _cashfree_event_payment(event)
    provider_order_id = order.get("order_id")
    provider_payment_id = payment_data.get("cf_payment_id")
    payment_status = str(payment_data.get("payment_status") or "").upper()

    if not provider_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing order id")

    payment = db.execute(
        select(Payment).where(
            Payment.provider == "CASHFREE",
            Payment.provider_order_id == provider_order_id,
        )
    ).scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    try:
        cf_order = cashfree_service.get_order(order_id=provider_order_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error while verifying webhook",
        )

    was_already_captured = payment.status == PaymentStatus.CAPTURED
    user_email = payment.booking.user.email
    booking_id = payment.booking_id
    result = _confirm_cashfree_payment(
        db,
        booking_id=booking_id,
        provider_order_id=provider_order_id,
        cf_order=cf_order,
        provider_payment_id=str(provider_payment_id) if provider_payment_id else None,
        raw_event=event,
        terminal_failure=payment_status in FAILED_PAYMENT_STATUSES,
        raise_on_incomplete=False,
    )

    if (
        result.status == BookingStatus.CONFIRMED.value
        and result.ticket_codes
        and user_email
        and not was_already_captured
    ):
        background_tasks.add_task(
            send_booking_confirmation_email_sync,
            user_email,
            booking_id,
            result.ticket_codes,
        )

    return {"ok": True, "booking_id": result.booking_id, "status": result.status}
