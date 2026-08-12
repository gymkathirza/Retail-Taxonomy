"""Integration: Basic Auth required on /api/v1/*; health stays public."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


def _api_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "alembic.ini").is_file():
            return parent
        if (parent / "apps" / "api" / "alembic.ini").is_file():
            return parent / "apps" / "api"
    raise RuntimeError("api root not found")


@pytest.fixture(scope="module")
def auth_client(engine):
    from alembic import command
    from alembic.config import Config
    import importlib

    api_root = _api_root()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    os.environ["DATABASE_URL"] = engine.url.render_as_string(hide_password=False)
    os.environ["DEMO_USER"] = "admin"
    os.environ["DEMO_PASSWORD"] = "password"
    command.upgrade(cfg, "head")

    import app.config as config_mod
    import app.db as db_mod
    import app.main as main_mod

    config_mod.get_settings.cache_clear()
    importlib.reload(config_mod)
    importlib.reload(db_mod)
    importlib.reload(main_mod)

    with TestClient(main_mod.app) as client:
        yield client


def test_health_public(auth_client: TestClient) -> None:
    assert auth_client.get("/health").status_code == 200
    assert auth_client.get("/health/ready").status_code == 200


def test_api_requires_auth(auth_client: TestClient) -> None:
    res = auth_client.get("/api/v1/zones")
    assert res.status_code == 401


def test_api_accepts_basic_auth(auth_client: TestClient) -> None:
    res = auth_client.get("/api/v1/zones", auth=("admin", "password"))
    assert res.status_code == 200
    assert "items" in res.json()
