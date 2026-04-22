import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sqlalchemy import select

from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.utils.security import hash_password


def seed_admin(email: str, password: str, full_name: str, phone: str | None, reset_password: bool) -> None:
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

        if user is None:
            user = User(
                full_name=full_name,
                email=email,
                phone=phone,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created admin user: id={user.id}, email={user.email}")
            return

        updated = False
        if user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            updated = True
        if not user.is_active:
            user.is_active = True
            updated = True
        if reset_password:
            user.password_hash = hash_password(password)
            updated = True
        if phone and user.phone != phone:
            user.phone = phone
            updated = True

        if updated:
            db.commit()
            print(f"Updated admin user: id={user.id}, email={user.email}")
        else:
            print(f"Admin user already present: id={user.id}, email={user.email}")
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed or update an admin user")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--full-name", default="System Admin", help="Admin full name")
    parser.add_argument("--phone", default=None, help="Admin phone number")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset password if user already exists",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    seed_admin(
        email=args.email,
        password=args.password,
        full_name=args.full_name,
        phone=args.phone,
        reset_password=args.reset_password,
    )
