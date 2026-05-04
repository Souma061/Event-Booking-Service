"""
Refresh token endpoint for the Event Booking Service.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.enhanced_security import verify_refresh_token, REFRESH_TOKEN_COOKIE_NAME, AUTH_COOKIE_NAME, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/refresh", status_code=200)
async def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    """
    # Get refresh token from cookies
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided"
        )

    try:
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)

        # Get user ID from payload
        user_id = payload["sub"]

        # Create new access token
        new_access_token = create_access_token(user_id)

        # Set new access token in response cookie
        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value=new_access_token,
            httponly=True,
            max_age=15*60,  # 15 minutes
            expires=15*60,
            samesite="lax",
            secure=True,
        )

        return {"message": "Access token refreshed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )