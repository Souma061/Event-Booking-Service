"""
Enhanced session management with refresh token support.
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

AUTH_COOKIE_NAME = "ev_auth_token"
REFRESH_TOKEN_COOKIE_NAME = "ev_refresh_token"

def hash_password(password: str) -> str:
    """Hash a password using pbkdf2_sha256."""
    return pwd_context.hash(password)

def verify_password(normal_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(normal_password, hashed_password)

def create_access_token(subject: str, expires_delta: timedelta = None) -> str:
    """
    Create an access token with expiration.

    Args:
        subject: User ID or identifier
        expires_delta: Optional timedelta for token expiration

    Returns:
        JWT access token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: str) -> str:
    """
    Create a refresh token for extended sessions.

    Args:
        subject: User ID or identifier

    Returns:
        JWT refresh token string
    """
    payload = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),  # 30-day refresh token
        "type": "refresh"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_access_token(token: str) -> dict:
    """
    Verify and decode an access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_refresh_token(token: str) -> dict:
    """
    Verify and decode a refresh token.

    Args:
        token: JWT refresh token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )