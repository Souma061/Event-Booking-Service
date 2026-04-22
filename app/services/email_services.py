import asyncio
import logging
from email.message import EmailMessage

import aiosmtplib
from app.config import settings

logger = logging.getLogger(__name__)


async def send_booking_confirmation_email(to_email: str,booking_id:int, ticket_codes: list[str]) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_SENDER_EMAIL:
        logger.warning("SMTP settings are not configured. Skipping email sending.")
        return

    msg = EmailMessage()
    msg["From"] = f"{settings.SMTP_SENDER_NAME} <{settings.SMTP_SENDER_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = f"Booking Confirmation - Booking ID: {booking_id}"
    ticket_list = "\n".join(f"- {code}" for code in ticket_codes)
    msg.set_content(f"Thank you for your booking! Your booking ID is {booking_id}.\n\nYour ticket codes:\n{ticket_list}\n\nPlease keep this email for your records.")

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD or None,
            start_tls=True
        )
    except Exception as e:
        logger.warning(f"SMTP email logic failed (Fake or missing credentials): {e}")


def send_booking_confirmation_email_sync(to_email: str,booking_id:int, ticket_codes: list[str]) -> None:
    try:
        asyncio.run(send_booking_confirmation_email(to_email,booking_id,ticket_codes))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(send_booking_confirmation_email(to_email,booking_id,ticket_codes))
        loop.close()
