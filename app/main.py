from collections import defaultdict

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
from app.utils.rate_limit import TokenBucket, get_rate_limit_client_ip, parse_rate_limit


_ = models

default_capacity, default_refill_rate = parse_rate_limit(settings.RATE_LIMIT_DEFAULT)
default_buckets = defaultdict(
    lambda: TokenBucket(capacity=default_capacity, refill_rate=default_refill_rate)
)
rate_limit_exempt_paths = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

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
                headers={"Retry-After": str(bucket.retry_after_seconds())},
            )

    return await call_next(request)

app.add_middleware(BaseHTTPMiddleware, dispatch=apply_default_rate_limit)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
