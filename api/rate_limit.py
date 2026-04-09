import os
import threading
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    def __init__(self):
        self._events = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int):
        now = time.time()
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= now - window_seconds:
                bucket.popleft()

            allowed = len(bucket) < limit
            if allowed:
                bucket.append(now)

            remaining = max(0, limit - len(bucket))
            retry_after = 0
            if bucket and not allowed:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))

            return allowed, remaining, retry_after


rate_limiter = InMemoryRateLimiter()

LOGIN_LIMIT = int(os.getenv("LOGIN_RATE_LIMIT", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", str(15 * 60)))
API_LIMIT = int(os.getenv("API_RATE_LIMIT", "100"))
API_WINDOW_SECONDS = int(os.getenv("API_RATE_WINDOW_SECONDS", "60"))
