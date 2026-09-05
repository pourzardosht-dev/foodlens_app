from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


class FixedWindowRateLimiter:
    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def __call__(self, request: Request) -> None:
        forwarded = request.headers.get("x-real-ip")
        client = forwarded or (request.client.host if request.client else "unknown")
        key = f"{request.url.path}:{client}"
        now = monotonic()
        threshold = now - self._window_seconds
        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= threshold:
                requests.popleft()
            if len(requests) >= self._limit:
                retry_after = max(1, int(requests[0] + self._window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)},
                )
            requests.append(now)


profile_creation_rate_limit = FixedWindowRateLimiter(
    limit=10, window_seconds=60 * 60
)
recognition_rate_limit = FixedWindowRateLimiter(limit=30, window_seconds=60)
export_rate_limit = FixedWindowRateLimiter(limit=5, window_seconds=60 * 60)