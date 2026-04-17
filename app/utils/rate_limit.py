# #NOTE:Phase 1 → build your own in-memory Token Bucket
# Phase 2 → move bucket state to Redis
# Phase 3 → compare with SlowAPI

# Login:
# capacity = 5
# refill = 1 token / 12 sec

# Booking:
# capacity = 3
# refill = 1 token / 20 sec

import time
from collections import defaultdict

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


# buckets = defaultdict(lambda: TokenBucket(capacity=5, refill_rate=1/12))

login_buckets = defaultdict(lambda: TokenBucket(capacity=5, refill_rate=1/12))
booking_buckets = defaultdict(lambda: TokenBucket(capacity=3, refill_rate=1/20))
