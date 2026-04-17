from datetime import datetime, timedelta,timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.models.event import Event,Show


def get_rule_based_recommentdations(db: Session, user_id: int, limit: int = 5) -> list[dict]:
    preferred_category_rows = db.execute(
        select(Event.category).join(Show,Show.event_id == Event.id).join(Booking, Booking.show_id == Show.id).where(
            Booking.user_id == user_id,
            Booking.status == BookingStatus.CONFIRMED
        )
    ).all()

    preferred_categories = {row[0] for row in preferred_category_rows if row[0] }
    now = datetime.now(timezone.utc)

    rows = db.execute(
        select(Show, Event).join(Event, Show.event_id == Event.id).where(
            Show.start_at >= now,
            Show.status == "ACTIVE",
        )
    ).all()

    scored = []
    for show,event in rows:
        category_match = event.category in preferred_categories
        score = 100 if category_match else 10
        reason = "Category match" if category_match else "No category match"
        scored.append((score,show.start_at, show, event, reason))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top_rows = scored[:limit]

    return [
        {
            "show_id": show.id,
            "event_id": event.id,
            "event_name": event.name,
            "category": event.category,
            "start_at": show.start_at.isoformat(),
            "reason": reason
        }
        for _, _, show, event, reason in top_rows
    ]
