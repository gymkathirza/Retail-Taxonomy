"""structlog JSON logging for API requests and CRUD events."""

from __future__ import annotations

import time
import uuid
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("retail-taxonomy-api")


def get_logger():
    return logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        response: Response | None = None
        outcome = "success"
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                outcome = "error"
            return response
        except Exception:
            outcome = "error"
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            user = getattr(request.state, "user", None)
            # First positional arg is structlog's reserved `event` field.
            logger.info(
                "http_request",
                service="retail-taxonomy-api",
                request_id=request_id,
                user=user,
                resource=request.url.path,
                duration_ms=duration_ms,
                outcome=outcome,
                method=request.method,
            )
            if response is not None:
                response.headers["X-Request-Id"] = request_id


def log_crud(
    *,
    event: str,
    resource: str,
    resource_id: str | None,
    outcome: str,
    request: Request | None = None,
    user: str | None = None,
) -> None:
    request_id = None
    if request is not None:
        request_id = getattr(request.state, "request_id", None)
        user = user or getattr(request.state, "user", None)
    # First positional becomes JSON `event` (structlog convention).
    logger.info(
        event,
        service="retail-taxonomy-api",
        request_id=request_id,
        user=user,
        resource=resource,
        resource_id=resource_id,
        outcome=outcome,
    )
