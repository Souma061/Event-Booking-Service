from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.booking import Booking, Ticket, Payment
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

booking = db.query(Booking).filter(Booking.id == 10).first()
if booking:
    print(f"Booking 10 Status: {booking.status}")
    tickets = db.query(Ticket).filter(Ticket.booking_id == 10).all()
    print(f"Tickets generated: {len(tickets)}")
    payments = db.query(Payment).filter(Payment.booking_id == 10).all()
    for p in payments:
        print(f"Payment {p.id}: {p.status}")
else:
    print("Booking 10 not found.")
