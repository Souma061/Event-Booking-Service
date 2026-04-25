from fastapi import APIRouter, Depends, HTTPException, Request, status
from hmac import compare_digest
from sqlalchemy import select
from sqlalchemy.orm import Session

import logging

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, Userout
from app.utils.rate_limit import get_rate_limit_client_ip, login_buckets, rate_limit_headers
from app.utils.security import create_access_token, hash_password, verify_password


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _get_login_rate_limit_key(request: Request, email: str) -> str:
    client_ip = get_rate_limit_client_ip(request)
    return f"{client_ip}:{email.lower()}"


def _authenticate_user(payload: LoginRequest, request: Request, db: Session) -> User:
    # Limit attempts per IP + email pair to slow down brute-force login abuse.
    rate_limit_key = _get_login_rate_limit_key(request, payload.email)
    bucket = login_buckets[rate_limit_key]
    if not bucket.allow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers=rate_limit_headers(bucket),
        )

    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    return user


def _token_for_user(user: User) -> TokenResponse:
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/register", response_model=Userout, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        role = UserRole.CUSTOMER
        if payload.admin_secret:
            expected_secret = settings.ADMIN_SECRET_KEY
            if not expected_secret:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin signup is disabled",
                )
            if not compare_digest(payload.admin_secret, expected_secret):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin secret key")
            role = UserRole.ADMIN

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            password_hash=hash_password(payload.password),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in register: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    try:
        user = _authenticate_user(payload, request, db)
        return _token_for_user(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    try:
        user = _authenticate_user(payload, request, db)
        if user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
        return _token_for_user(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/me", response_model=Userout)
def get_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user