from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
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
