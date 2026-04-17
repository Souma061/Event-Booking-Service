from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.event import Venue,Event, Show, SeatCategoryInventory
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventOut,
    InventoryRowIn,
    InventoryRowOut,
    ShowCreate,
    ShowOut,
    VenueCreate,
    VenueOut
    )


router = APIRouter(prefix="/api/events", tags=["Events"])

@router.post("/venues", response_model = VenueOut,status_code=status.HTTP_201_CREATED)
def create_venue(payload = VenueCreate,db: Session = Depends(get_db),_: User = Depends(require_admin)):
    venue = Venue(name = payload.name,city = payload.city,address = payload.address)
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue

@router.post("", response_model=EventOut,status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db), admin_user : User = Depends(require_admin)):
    venue = db.get(Venue, payload.venue_id)
    if not venue:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid venue_id")

    event = Event(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        venue_id=payload.venue_id,
        created_by=admin_user.id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/shows", response_model=ShowOut, status_code=status.HTTP_201_CREATED)
def create_show(event_id: int, payload: ShowCreate,db: Session = Depends(get_db), _: User = Depends(require_admin)):
    event = db.get(Event,event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event_id")

    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_at must be after start_at")

    show = Show(
        event_id = event_id,
        start_at = payload.start_at,
        end_at = payload.end_at,
        # total_seats = payload.total_seats
        status = payload.status
    )
    db.add(show)
    db.commit()
    db.refresh(show)
    return show

@router.put("/shows/{show_id}/inventory", response_model=list[InventoryRowOut])
def upsert_show_inventory(
    show_id:int,
    payload: list[InventoryRowIn],
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    show = db.get(Show,show_id)
    if not show:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid show_id")

    out_rows = []
    for row in payload:
        inv = db.execute(
            select(SeatCategoryInventory).where(
                SeatCategoryInventory.show_id == show_id,
                SeatCategoryInventory.category == row.category
            )
        ).scalar_one_or_none()

        if inv:
            already_sold = inv.total_seats - inv.available_seats
            if row.total_seats < already_sold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot reduce total_seats below already sold seats ({already_sold}) for category {row.category}"
                )
            inv.total_seats = row.total_seats
            inv.available_seats = row.total_seats - already_sold
        else:
            inv = SeatCategoryInventory(
                show_id = show_id,
                category = row.category,
                total_seats = row.total_seats,
                available_seats = row.total_seats
            )
            db.add(inv)
        out_rows.append(inv)
    db.commit()
    for inv in out_rows:
        db.refresh(inv)
    return out_rows


@router.get("/{event_id}/shows", response_model=list[ShowOut])
def list_event_shows(
    event_id:int,
    db: Session = Depends(get_db)
):
    event = db.get(Event,event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event_id")

    shows = db.execute(select(Show).where(Show.event_id == event_id)).scalars().all()
    return shows
