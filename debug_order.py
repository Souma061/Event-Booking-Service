import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.booking import Booking
from app.services.payment_service import razorpay_service
import secrets

engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/event_booking")
Session = sessionmaker(bind=engine)
db = Session()
booking = db.query(Booking).filter(Booking.id == 4).first()
if not booking:
    print("Booking 4 not found")
    sys.exit(1)

print(f"Booking amount: {booking.total_amount}, type: {type(booking.total_amount)}")

try:
    order = razorpay_service.create_order(
        amount=booking.total_amount,
        receipt=f"booking_{booking.id}_{secrets.token_hex(8)}",
        currency=booking.currency,
        notes={"booking_id": str(booking.id), "user_id": str(booking.user_id)},
    )
    print("Order created:", order)
except Exception as e:
    import traceback
    traceback.print_exc()
