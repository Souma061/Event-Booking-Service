import subprocess
import sys
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.booking import Ticket
from app.models.enums import TicketStatus

router = APIRouter(prefix="/api/admin", tags=["admin"])

class TicketVerifyRequest(BaseModel):
    ticket_code: str

class TicketVerifyResponse(BaseModel):
    status: str
    message: str
    ticket_id: int | None = None
    booking_id: int | None = None
    show_id: int | None = None

@router.post("/verify-ticket", response_model=TicketVerifyResponse)
def verify_ticket(
    payload: TicketVerifyRequest,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    ticket = db.execute(
        select(Ticket).where(Ticket.ticket_code == payload.ticket_code).with_for_update()
    ).scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Invalid ticket code. Ticket not found."
        )
    
    if ticket.status == TicketStatus.USED:
        return TicketVerifyResponse(
            status="ALREADY_USED",
            message="This ticket has already been scanned and used for entry.",
            ticket_id=ticket.id,
            booking_id=ticket.booking_id,
            show_id=ticket.show_id
        )
        
    if ticket.status == TicketStatus.CANCELLED:
        return TicketVerifyResponse(
            status="CANCELLED",
            message="This ticket was cancelled and is invalid.",
            ticket_id=ticket.id,
            booking_id=ticket.booking_id,
            show_id=ticket.show_id
        )
        
    if ticket.status == TicketStatus.EXPIRED:
        return TicketVerifyResponse(
            status="EXPIRED",
            message="This ticket is expired.",
            ticket_id=ticket.id,
            booking_id=ticket.booking_id,
            show_id=ticket.show_id
        )

    # Valid ticket
    ticket.status = TicketStatus.USED
    db.commit()
    
    return TicketVerifyResponse(
        status="VALID",
        message="Valid entry! Ticket marked as used.",
        ticket_id=ticket.id,
        booking_id=ticket.booking_id,
        show_id=ticket.show_id
    )


class MigrationResponse(BaseModel):
    status: str
    message: str
    applied: list[str] = []


@router.post("/run-migrations", response_model=MigrationResponse)
def run_migrations(admin_user=Depends(require_admin)):
    """One-time admin endpoint to run pending Alembic migrations."""
    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    output_messages = []

    try:
        from app.database import engine
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if "alembic_version" not in tables and "users" in tables:
            # Database was created by create_all(), so stamp the initial migration
            stamp = subprocess.run(
                [sys.executable, "-m", "alembic", "stamp", "126b25d4eb52"],
                capture_output=True, text=True, cwd=cwd
            )
            output_messages.append(f"Stamping initial schema: {stamp.stdout.strip() or stamp.stderr.strip()}")
    except Exception as e:
        output_messages.append(f"Auto-stamp check failed: {e}")

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True, text=True, cwd=cwd
    )

    if result.returncode == 0:
        output_messages.append(result.stdout.strip() or "No migrations to apply")
        return MigrationResponse(
            status="success",
            message="\n".join(output_messages),
        )

    return MigrationResponse(
        status="error",
        message=f"Migration failed: {result.stderr or result.stdout}\nPrevious logs: {output_messages}",
    )
