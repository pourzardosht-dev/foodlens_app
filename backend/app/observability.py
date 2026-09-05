import json
import logging
from collections import defaultdict
from contextvars import ContextVar
from threading import Lock
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response


logger = logging.getLogger("foodlens")
request_id_context: ContextVar[str] = ContextVar("request_id", default="unknown")
_metrics_lock = Lock()
_request_counts: dict[tuple[str, str, int], int] = defaultdict(int)
_request_duration_seconds: dict[tuple[str, str], float] = defaultdict(float)


async def observe_request(request: Request, call_next) -> Response:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    token = request_id_context.set(request_id[:128])
    started_at = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id_context.get()
        return response
    finally:
        duration = perf_counter() - started_at
        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")
        with _metrics_lock:
            _request_counts[(request.method, route_path, status_code)] += 1
            _request_duration_seconds[(request.method, route_path)] += duration
        request_id_context.reset(token)


def audit_event(event: str) -> None:
    logger.info(
        json.dumps(
            {"event": event, "request_id": request_id_context.get()},
            separators=(",", ":"),
        )
    )


def render_metrics() -> str:
    lines = [
        "# HELP foodlens_http_requests_total HTTP requests by route and status.",
        "# TYPE foodlens_http_requests_total counter",
    ]
    with _metrics_lock:
        for (method, route, status_code), value in sorted(_request_counts.items()):
            labels = f'method="{method}",route="{route}",status="{status_code}"'
            lines.append(f"foodlens_http_requests_total{{{labels}}} {value}")
        lines.extend(
            [
                "# HELP foodlens_http_request_duration_seconds_total Total HTTP request duration by route.",
                "# TYPE foodlens_http_request_duration_seconds_total counter",
            ]
        )
        for (method, route), value in sorted(_request_duration_seconds.items()):
            labels = f'method="{method}",route="{route}"'
            lines.append(
                f"foodlens_http_request_duration_seconds_total{{{labels}}} {value:.6f}"
            )
    return "\n".join(lines) + "\n"