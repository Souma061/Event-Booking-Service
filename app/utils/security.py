from datetime import datetime,timedelta,timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(normal_password:str,hashed_password:str) ->bool:
    return pwd_context.verify(normal_password, hashed_password)


def create_access_token(subject:str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "exp": expires_at
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token:str) -> dict:
    try:
        payload = jwt.decode(token=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
