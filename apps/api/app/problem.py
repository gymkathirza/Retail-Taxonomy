"""RFC 7807 problem+json helpers."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def problem_response(
    *,
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    instance: str | None = None,
    extra: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
    }
    if instance is not None:
        body["instance"] = instance
    if extra:
        body.update(extra)
    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    title = {404: "Not Found", 409: "Conflict", 422: "Unprocessable Entity"}.get(
        exc.status_code, "Error"
    )
    type_ = "about:blank"
    if exc.status_code == 409:
        type_ = "https://example.com/problems/duplicate-name"
        if "inactive parent" in detail.lower() or "parent is inactive" in detail.lower():
            type_ = "https://example.com/problems/inactive-parent"
    return problem_response(
        status=exc.status_code,
        title=title,
        detail=detail,
        type_=type_,
        instance=str(request.url.path),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return problem_response(
        status=422,
        title="Unprocessable Entity",
        detail="Request validation failed",
        instance=str(request.url.path),
        extra={"errors": exc.errors()},
    )
