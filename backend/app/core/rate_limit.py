"""A small in-process sliding-window rate limiter.

Good enough for a single backend instance (Render free/starter tier). For a
horizontally scaled deployment swap this for a shared store such as Redis.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: float = 60.0) -> None:
        if limit <= 0:
            return
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(self._hits) > 10_000:
                # Bound memory: forget keys with no recent hits.
                for stale in [k for k, v in self._hits.items() if k != key and (not v or now - v[-1] > window_seconds)]:
                    del self._hits[stale]
            if len(hits) >= limit:
                retry_after = int(window_seconds - (now - hits[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please slow down and try again shortly.",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    # X-Forwarded-For is deliberately NOT read here: clients can forge it. Behind a
    # trusted reverse proxy, uvicorn's --proxy-headers (limited by FORWARDED_ALLOW_IPS)
    # rewrites request.client to the real address before we see it.
    return request.client.host if request.client else "unknown"
