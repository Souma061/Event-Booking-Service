# #NOTE:Phase 1 → build your own in-memory Token Bucket
# Phase 2 → move bucket state to Redis
# Phase 3 → compare with SlowAPI

# Login:
# capacity = 5
# refill = 1 token / 12 sec

# Booking:
# capacity = 3
# refill = 1 token / 20 sec

import hashlib
import logging
import math
import time
from typing import Protocol

from fastapi import Request

from app.config import settings

try:
    import redis
    from redis import Redis
except ImportError:
    redis = None
    Redis = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


def parse_rate_limit(value: str) -> tuple[int, float, int]:
    """Parse a rate limit string like ``"10/minute"``.

    Returns ``(capacity, refill_rate, window_seconds)`` so callers can use
    the original configured window directly instead of reconstructing it
    from ``capacity / refill_rate`` (which is subject to float rounding).
    """
    amount_text, _, window_text = value.partition("/")
    if not amount_text or not window_text:
        raise ValueError(f"Invalid rate limit format: {value}")

    amount = int(amount_text)
    if amount < 1:
        raise ValueError("Rate limit amount must be at least 1")

    window = window_text.strip().lower()
    seconds_by_window = {
        "second": 1,
        "sec": 1,
        "minute": 60,
        "min": 60,
        "hour": 3600,
        "day": 86400,
    }
    if window not in seconds_by_window:
        raise ValueError(f"Unsupported rate limit window: {window_text}")

    window_seconds = seconds_by_window[window]
    return amount, amount / window_seconds, window_seconds


class RateLimitBucket(Protocol):
    capacity: int

    def allow(self) -> bool: ...
    def remaining(self) -> int: ...
    def retry_after_seconds(self) -> int: ...
    def reset_after_seconds(self) -> int: ...


class TokenBucket:
    def __init__(self, capacity:int, refill_rate:float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill_time = time.time()
        self.last_seen_time = self.last_refill_time

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill_time

        self.tokens = min(
            self.capacity, self.tokens + elapsed * self.refill_rate
            )
        self.last_refill_time = now
        self.last_seen_time = now

    def allow(self) -> bool:
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def remaining(self) -> int:
        self._refill()
        return max(0, math.floor(self.tokens))

    def retry_after_seconds(self) -> int:
        self._refill()
        if self.tokens >= 1:
            return 0
        return max(1, math.ceil((1 - self.tokens) / self.refill_rate))

    def reset_after_seconds(self) -> int:
        self._refill()
        missing_tokens = self.capacity - self.tokens
        if missing_tokens <= 0:
            return 0
        return max(1, math.ceil(missing_tokens / self.refill_rate))


class BucketStore:
    def __init__(self, capacity: int, refill_rate: float, cleanup_interval: int = 250):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.cleanup_interval = cleanup_interval
        self.buckets: dict[str, TokenBucket] = {}
        self.access_count = 0
        self.idle_ttl_seconds = max(600, math.ceil((capacity / refill_rate) * 2))

    def __getitem__(self, key: str) -> TokenBucket:
        self.access_count += 1
        if self.access_count % self.cleanup_interval == 0:
            self.cleanup()

        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(capacity=self.capacity, refill_rate=self.refill_rate)
            self.buckets[key] = bucket
        return bucket

    def cleanup(self) -> None:
        cutoff = time.time() - self.idle_ttl_seconds
        stale_keys = [
            key for key, bucket in self.buckets.items()
            if bucket.last_seen_time < cutoff
        ]
        for key in stale_keys:
            del self.buckets[key]


_LIMITER_LUA_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return { current, ttl }
"""


class ValkeyFixedWindowBucket:
    def __init__(
        self,
        client: "Redis",
        namespace: str,
        key: str,
        capacity: int,
        window_seconds: int,
        fail_open: bool,
        limiter_script,
    ):
        self.client = client
        self.namespace = namespace
        self.key = key
        self.capacity = capacity
        self.window_seconds = window_seconds
        self.fail_open = fail_open
        self._limiter_script = limiter_script
        self._last_count: int | None = None
        self._last_ttl: int | None = None

    @property
    def redis_key(self) -> str:
        window_id = int(time.time()) // self.window_seconds
        digest = hashlib.sha256(self.key.encode("utf-8")).hexdigest()
        return f"rate_limit:{self.namespace}:{digest}:{window_id}"

    def _fail_open(self, exc: Exception) -> bool:
        logger.warning("Valkey rate limiter unavailable: %s", exc)
        if self.fail_open:
            # Pretend the limiter saw no usage so the request proceeds and
            # response headers reflect the full capacity being available.
            self._last_count = 0
            self._last_ttl = 0
            return True

        # Fail closed: deny the request and populate cached state so that
        # rate_limit_headers() reports a consistent 429 response without
        # issuing additional Redis commands against the unreachable server.
        self._last_count = self.capacity + 1
        self._last_ttl = self.window_seconds
        return False

    def allow(self) -> bool:
        try:
            count, ttl = self._limiter_script(
                keys=[self.redis_key],
                args=[self.window_seconds],
                client=self.client,
            )
        except Exception as exc:
            return self._fail_open(exc)

        self._last_count = int(count)
        # TTL can be -1 (no expire) or -2 (missing); clamp to >= 0.
        self._last_ttl = max(0, int(ttl))
        return self._last_count <= self.capacity

    def _current_count_and_ttl(self) -> tuple[int, int]:
        if self._last_count is not None and self._last_ttl is not None:
            return self._last_count, self._last_ttl

        try:
            pipe = self.client.pipeline()
            key = self.redis_key
            pipe.get(key)
            pipe.ttl(key)
            count_value, ttl_value = pipe.execute()
            count = int(count_value or 0)
            ttl = max(0, int(ttl_value or 0))
            # Cache so follow-up header lookups don't re-query Redis.
            self._last_count = count
            self._last_ttl = ttl
            return count, ttl
        except Exception as exc:
            logger.warning("Valkey rate limiter headers unavailable: %s", exc)
            # Populate a safe fallback so repeated header calls don't keep
            # hammering an unreachable server for the same request.
            self._last_count = 0
            self._last_ttl = 0
            return 0, 0

    def remaining(self) -> int:
        count, _ = self._current_count_and_ttl()
        return max(0, self.capacity - count)

    def retry_after_seconds(self) -> int:
        count, ttl = self._current_count_and_ttl()
        if count < self.capacity:
            return 0
        # Guarantee a non-zero retry hint when the limit has been reached,
        # mirroring the in-memory TokenBucket behaviour.
        return max(1, ttl)

    def reset_after_seconds(self) -> int:
        _, ttl = self._current_count_and_ttl()
        return ttl


class ValkeyBucketStore:
    def __init__(
        self,
        namespace: str,
        capacity: int,
        refill_rate: float,
        url: str,
        fail_open: bool = True,
        window_seconds: int | None = None,
        health_check: bool = True,
    ):
        if redis is None:
            raise RuntimeError("redis package is required for Valkey-backed rate limiting")

        self.namespace = namespace
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.window_seconds = (
            window_seconds
            if window_seconds and window_seconds > 0
            else max(1, math.ceil(capacity / refill_rate))
        )
        self.fail_open = fail_open
        # socket_connect_timeout keeps the startup ping from blocking the
        # process for long if Valkey is unreachable. socket_timeout caps the
        # per-command latency in the request hot path so a slow Valkey
        # degrades quickly to fail-open instead of stalling every request.
        self.client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=0.5,
        )

        if health_check:
            # Force a real connection so build_bucket_store() can catch
            # startup failures and fall back to the in-memory limiter.
            self.client.ping()

        # Register the Lua script once so subsequent invocations use EVALSHA.
        self._limiter_script = self.client.register_script(_LIMITER_LUA_SCRIPT)

    def __getitem__(self, key: str) -> ValkeyFixedWindowBucket:
        return ValkeyFixedWindowBucket(
            client=self.client,
            namespace=self.namespace,
            key=key,
            capacity=self.capacity,
            window_seconds=self.window_seconds,
            fail_open=self.fail_open,
            limiter_script=self._limiter_script,
        )


def build_bucket_store(
    namespace: str,
    capacity: int,
    refill_rate: float,
    window_seconds: int | None = None,
) -> BucketStore | ValkeyBucketStore:
    if settings.VALKEY_URL:
        try:
            return ValkeyBucketStore(
                namespace=namespace,
                capacity=capacity,
                refill_rate=refill_rate,
                url=settings.VALKEY_URL,
                fail_open=settings.RATE_LIMIT_FAIL_OPEN,
                window_seconds=window_seconds,
            )
        except Exception as exc:
            logger.warning("Falling back to in-memory rate limiter for %s: %s", namespace, exc)

    return BucketStore(capacity=capacity, refill_rate=refill_rate)


def get_rate_limit_client_ip(request: Request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_headers(bucket: RateLimitBucket) -> dict[str, str]:
    retry_after = bucket.retry_after_seconds()
    return {
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": str(bucket.capacity),
        "X-RateLimit-Remaining": str(bucket.remaining()),
        "X-RateLimit-Reset": str(bucket.reset_after_seconds()),
    }


login_capacity, login_refill_rate, login_window_seconds = parse_rate_limit(settings.RATE_LIMIT_LOGIN)
booking_capacity, booking_refill_rate, booking_window_seconds = parse_rate_limit(settings.RATE_LIMIT_BOOKING)

login_buckets = build_bucket_store(
    "login",
    capacity=login_capacity,
    refill_rate=login_refill_rate,
    window_seconds=login_window_seconds,
)
booking_buckets = build_bucket_store(
    "booking",
    capacity=booking_capacity,
    refill_rate=booking_refill_rate,
    window_seconds=booking_window_seconds,
)
