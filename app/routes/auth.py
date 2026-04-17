from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, Userout
from app.utils.rate_limit import login_buckets
from app.utils.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _get_login_rate_limit_key(request: Request, email: str) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else request.client.host if request.client else "unknown"
    )
    return f"{client_ip}:{email.lower()}"


@router.post("/register", response_model=Userout, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        full_name = payload.full_name,
        email = payload.email,
        phone = payload.phone,
        password_hash = hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Limit attempts per IP + email pair to slow down brute-force login abuse.
    rate_limit_key = _get_login_rate_limit_key(request, payload.email)
    bucket = login_buckets[rate_limit_key]
    if not bucket.allow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(bucket.retry_after_seconds())},
        )

    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=Userout)
def get_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user
