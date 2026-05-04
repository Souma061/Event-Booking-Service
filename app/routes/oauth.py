import logging
import httpx
from fastapi import APIRouter,Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from app.config import settings
from itsdangerous import URLSafeTimedSerializer,BadSignature,SignatureExpired
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import UserRole
from app.utils.enhanced_security import AUTH_COOKIE_NAME, create_access_token, create_refresh_token
from  app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth",tags = ["OAuth"])
_signer = URLSafeTimedSerializer(settings.OAUTH_STATE_SECRET)

#helper function
def _sign_state(provider: str) -> str:
    return _signer.dumps({"provider": provider})

def _unsign_state(state: str, ) -> str:
    try:
        data = _signer.loads(state, max_age=600) # state valid for 10 minutes
        return data["provider"]
    except (BadSignature, SignatureExpired) as e:
        raise HTTPException(status_code=400, detail="Invalid or expired state") from e


def _upsert_user(db: Session, email:str,name:str, provider:str,sub:str) -> User:
    """Find existing user by email or create new one"""
    user = db.execute(
        select(User).where(User.oauth_provider == provider, User.oauth_sub == sub)
    ).scalar_one_or_none()
    if user:
        return user

    #email already registered via email/password. so link auth to that account
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    if user:
        user.oauth_provider = provider
        user.oauth_sub = sub
        db.commit()
        db.refresh(user)
        return user

    # new user
    user = User(
        email=email,
        full_name=name or email.split("@")[0],
        password_hash=None,  # no password for OAuth users
        role=UserRole.CUSTOMER,
        oauth_provider=provider,
        oauth_sub=sub
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token_redirect(user: User) -> RedirectResponse:
    token = create_access_token(str(user.id))
    response = RedirectResponse(settings.OAUTH_FRONTEND_REDIRECT_URL)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=settings.APP_ENV == "prod",
    )
    response.set_cookie(
        key="ev_refresh_token",
        value=create_refresh_token(str(user.id)),
        httponly=True,
        max_age=30*24*60*60,
        expires=30*24*60*60,
        samesite="lax",
        secure=settings.APP_ENV == "prod",
    )
    return response


def _get_callback_url(request: Request, provider: str) -> str:
    """Dynamically construct the callback URL based on the incoming request's host"""
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/api/auth/{provider}/callback"


# Google routes
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL= "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

@router.get("/google/login")
def google_login(request: Request):
    state = _sign_state("google")
    redirect_uri = _get_callback_url(request, "google")
    params = (
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid+email+profile"
        f"&state={state}"
        f"&access_type=offline"
    )
    return RedirectResponse(GOOGLE_AUTH_URL + "?" + params)


@router.get("/google/callback")
def google_callback(request: Request, code:str, state:str,db:Session=Depends(get_db)):
    _unsign_state(state)
    redirect_uri = _get_callback_url(request, "google")

    with httpx.Client() as client:
        # exchange code for tokens
        token_response = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code":code,
                "client_id":settings.GOOGLE_CLIENT_ID,
                "client_secret":settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri":redirect_uri,
                "grant_type":"authorization_code"
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")

        userinfo = client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()
    email = userinfo.get("email")
    name = userinfo.get("name")
    sub = userinfo.get("sub")

    if not email or not sub:
        raise HTTPException(status_code=400, detail="Failed to retrieve user info from Google")

    user = _upsert_user(db, email, name, "google", sub)
    return _token_redirect(user)



# Github OAuth routes can be implemented similarly by defining the appropriate endpoints and using GitHub's OAuth URLs and user info endpoints.

GITHUB_AUTH_URL="https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL="https://github.com/login/oauth/access_token"
GITHUB_USERINFO_URL="https://api.github.com/user"
GITHUB_EMAILS_URL="https://api.github.com/user/emails"


@router.get("/github/login")
def github_login(request: Request):
    state = _sign_state("github")
    redirect_uri = _get_callback_url(request, "github")
    params = (
        f"client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=read:user+user:email"
        f"&state={state}"
    )
    return RedirectResponse(GITHUB_AUTH_URL + "?" + params)

@router.get("/github/callback")
def github_callback(request: Request, code:str, state:str, db:Session=Depends(get_db)):
    _unsign_state(state)
    redirect_uri = _get_callback_url(request, "github")

    with httpx.Client() as client:
        token_response = client.post(
            GITHUB_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")

        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo = client.get(GITHUB_USERINFO_URL, headers=headers).json()

        email = userinfo.get("email")
        if not email:
            #if email is not public, fetch from separate endpoint
            emails_response = client.get(GITHUB_EMAILS_URL, headers=headers).json()
            primary_emails = next((e for e in emails_response if e.get("primary") and e.get("verified")), None) # it is possible that user has no primary email or primary email is not verified. in that case we will just take the first verified email
            if primary_emails:
                email = primary_emails.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Failed to retrieve user email from GitHub")

    sub = str(userinfo.get("id"))
    name = userinfo.get("name") or userinfo.get("login") or email.split("@")[0] # fallback to username or email prefix if name is not available
    user = _upsert_user(db, email=email, name=name, provider="github", sub=sub)
    return _token_redirect(user)
