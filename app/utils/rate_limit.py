# #NOTE:Phase 1 → build your own in-memory Token Bucket
# Phase 2 → move bucket state to Redis
# Phase 3 → compare with SlowAPI

# Login:
# capacity = 5
# refill = 1 token / 12 sec

# Booking:
# capacity = 3
# refill = 1 token / 20 sec

import math
import time
from collections import defaultdict

from fastapi import Request

class TokenBucket:
    def __init__(self, capacity:int, refill_rate:float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill_time = time.time()

    def allow(self) -> bool:
        now = time.time()
        elapsed = now - self.last_refill_time

        self.tokens = min(
            self.capacity, self.tokens + elapsed * self.refill_rate
            )
        self.last_refill_time = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def retry_after_seconds(self) -> int:
        if self.tokens >= 1:
            return 0
        return max(1, math.ceil((1 - self.tokens) / self.refill_rate))


def get_rate_limit_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# buckets = defaultdict(lambda: TokenBucket(capacity=5, refill_rate=1/12))

login_buckets = defaultdict(lambda: TokenBucket(capacity=5, refill_rate=1/12))
booking_buckets = defaultdict(lambda: TokenBucket(capacity=3, refill_rate=1/20))


def parse_rate_limit(value: str) -> tuple[int, float]:
    amount_text, _, window_text = value.partition("/")
    if not amount_text or not window_text:
        raise ValueError(f"Invalid rate limit format: {value}")

    amount = int(amount_text)
    window = window_text.strip().lower()
    seconds_by_window = {
        "second": 1,
        "sec": 1,
        "minute": 60,
        "min": 60,
        "hour": 3600,
    }
    if window not in seconds_by_window:
        raise ValueError(f"Unsupported rate limit window: {window_text}")

    window_seconds = seconds_by_window[window]
    return amount, amount / window_seconds
