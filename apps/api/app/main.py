from fastapi import Depends, FastAPI, Response
from fastapi.exceptions import RequestValidationError
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

from app.auth import require_auth
from app.logging_setup import RequestLoggingMiddleware
from app.problem import http_exception_handler, validation_exception_handler
from app.routers import categories, departments, health, subcategories, taxonomy, zones


def _counter(name: str, documentation: str, labelnames: list[str]) -> Counter:
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return existing  # type: ignore[return-value]
    return Counter(name, documentation, labelnames)


def _histogram(name: str, documentation: str, labelnames: list[str]) -> Histogram:
    existing = REGISTRY._names_to_collectors.get(name)
    if existing is not None:
        return existing  # type: ignore[return-value]
    return Histogram(name, documentation, labelnames)


REQUEST_COUNT = _counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = _histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        path = request.url.path
        # Keep cardinality low for path labels
        if path.startswith("/api/v1/"):
            label_path = "/api/v1/*"
        else:
            label_path = path
        REQUEST_COUNT.labels(request.method, label_path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, label_path).observe(time.perf_counter() - start)
        return response


app = FastAPI(title="Retail Taxonomy API", version="0.1.0")
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(health.router)
app.include_router(health.details_router, dependencies=[Depends(require_auth)])

_auth = [Depends(require_auth)]
app.include_router(zones.router, dependencies=_auth)
app.include_router(departments.nested, dependencies=_auth)
app.include_router(departments.router, dependencies=_auth)
app.include_router(categories.nested, dependencies=_auth)
app.include_router(categories.router, dependencies=_auth)
app.include_router(subcategories.nested, dependencies=_auth)
app.include_router(subcategories.router, dependencies=_auth)
app.include_router(taxonomy.router, dependencies=_auth)


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
