from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ProblemException(Exception):
    def __init__(self, status: int, title: str, detail: str, type_: str = "about:blank"):
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type_


def _problem(status: int, title: str, detail: str, instance: str, type_: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": type_,
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        },
    )


def register_exception_handlers(app) -> None:
    @app.exception_handler(ProblemException)
    async def _handle_problem(request: Request, exc: ProblemException):
        return _problem(exc.status, exc.title, exc.detail, str(request.url.path), exc.type)

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(request: Request, exc: StarletteHTTPException):
        title = {404: "Not Found", 401: "Unauthorized", 403: "Forbidden"}.get(exc.status_code, "Error")
        return _problem(
            exc.status_code, title, str(exc.detail), str(request.url.path), "about:blank"
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            media_type="application/problem+json",
            content={
                "type": "about:blank",
                "title": "Unprocessable Entity",
                "status": 422,
                "detail": "Request validation failed.",
                "instance": str(request.url.path),
                "errors": exc.errors(),
            },
        )
