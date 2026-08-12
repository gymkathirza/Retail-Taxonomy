from fastapi import APIRouter, Response
from sqlalchemy import text

from app.db import SessionLocal, engine

router = APIRouter(tags=["health"])
details_router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(response: Response) -> dict[str, str]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "not_ready"}
    return {"status": "ready"}


@details_router.get("/details")
def health_details() -> dict:
    db_ok = False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_ok = True
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "degraded",
            "database": {"ok": False, "error": str(exc)},
            "engine": str(engine.url.render_as_string(hide_password=True)),
        }
    return {
        "status": "ok" if db_ok else "degraded",
        "database": {"ok": db_ok},
        "engine": str(engine.url.render_as_string(hide_password=True)),
    }
