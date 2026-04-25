import json
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from app import models
from app.config import settings
from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.booking import router as booking_router
from app.routes.events import router as events_router
from app.routes.payments import router as payments_router
from app.routes.admin import router as admin_router
from app.utils.rate_limit import build_bucket_store, get_rate_limit_client_ip, parse_rate_limit, rate_limit_headers


logger = logging.getLogger(__name__)
_ = models


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

default_capacity, default_refill_rate = parse_rate_limit(settings.RATE_LIMIT_DEFAULT)
default_buckets = build_bucket_store("default", capacity=default_capacity, refill_rate=default_refill_rate)
rate_limit_exempt_paths = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/payments/cashfree/webhook",
}

app = FastAPI(title=settings.APP_NAME)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_origin_regex=cors_allow_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)



@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(booking_router)
app.include_router(events_router)
app.include_router(payments_router)
app.include_router(admin_router)
