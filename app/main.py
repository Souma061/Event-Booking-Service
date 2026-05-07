import json
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models
from app.config import settings
from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.booking import router as booking_router
from app.routes.events import router as events_router
from app.routes.payments import router as payments_router
from app.routes.admin import router as admin_router
from app.utils.rate_limit import build_bucket_store, get_rate_limit_client_ip, parse_rate_limit, rate_limit_headers
from app.routes.refresh import router as refresh_router
from app.middleware.security_headers import SecurityHeadersMiddleware
import asyncio
from app.routes.oauth import router as oauth_router
from app.routes.notifications import router as notifications_router
from app.services.kafka_consumer import consume_notifications

logger = logging.getLogger(__name__)
_ = models


def log_security_event(event_name: str, details: dict, user_id: int | None = None) -> None:
    logger.info(
        "security_event=%s user_id=%s details=%s",
        event_name,
        user_id,
        details,
    )



def _parse_cors_allow_origins(raw_origins: str) -> list[str]:
    raw_origins = raw_origins.strip()
    if not raw_origins:
        return []

    candidates: list[str]
    try:
        parsed_json = json.loads(raw_origins)
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed_json = None

    if isinstance(parsed_json, str):
        candidates = [parsed_json]
    elif isinstance(parsed_json, list):
        candidates = [str(origin) for origin in parsed_json]
    else:
        candidates = raw_origins.replace("\n", ",").split(",")

    parsed: list[str] = []
    for origin in candidates:
        normalized = origin.strip().strip('"').strip("'").rstrip("/")
        if normalized:
            parsed.append(normalized)
    return parsed


cors_allow_origins = _parse_cors_allow_origins(settings.CORS_ALLOW_ORIGINS)
cors_allow_origin_regex = settings.CORS_ALLOW_ORIGIN_REGEX.strip() or None

if not cors_allow_origins and not cors_allow_origin_regex:
    logger.warning("CORS is enabled but no allowed origins are configured")

logger.info(
    "CORS configured with %d origin(s), regex=%s",
    len(cors_allow_origins),
    cors_allow_origin_regex or "<none>",
)

default_capacity, default_refill_rate, default_window_seconds = parse_rate_limit(settings.RATE_LIMIT_DEFAULT)
default_buckets = build_bucket_store(
    "default",
    capacity=default_capacity,
    refill_rate=default_refill_rate,
    window_seconds=default_window_seconds,
)
rate_limit_exempt_paths = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/payments/cashfree/webhook",
}


app = FastAPI(title=settings.APP_NAME)


# Exception handlers to ensure JSON responses for all errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log security-relevant exceptions
    log_security_event("unhandled_exception", {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "path": str(request.url),
        "method": request.method,
        "client": request.client.host if request.client else "unknown"
    }, request.state.current_user.id if hasattr(request.state, 'current_user') else None)

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An error occurred processing your request"},
    )


async def apply_default_rate_limit(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path not in rate_limit_exempt_paths:
        bucket = default_buckets[get_rate_limit_client_ip(request)]
        if not bucket.allow():
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers=rate_limit_headers(bucket),
            )

    return await call_next(request)


app.add_middleware(BaseHTTPMiddleware, dispatch=apply_default_rate_limit)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_origin_regex=cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    # allow_origin_regex=None,
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    asyncio.create_task(consume_notifications())


@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
async def health_check():
    # async so it yields to the event loop immediately and is never queued
    # behind sync handlers under high concurrency.
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(booking_router)
app.include_router(events_router)
app.include_router(payments_router)
app.include_router(admin_router)
app.include_router(oauth_router)
app.include_router(refresh_router)
app.include_router(notifications_router)
