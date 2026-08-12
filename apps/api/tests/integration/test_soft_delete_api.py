"""Integration: soft-delete, restore, and include_inactive via FastAPI."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "apps" / "api" / "alembic.ini").is_file():
            return parent
        if (parent / "alembic.ini").is_file():
            return parent
    raise RuntimeError("Could not locate repository root from test file")


REPO_ROOT = _repo_root()
API_ROOT = REPO_ROOT / "apps" / "api"
if not (API_ROOT / "alembic.ini").is_file():
    API_ROOT = Path("/app")


@pytest.fixture(scope="module")
def api_client(engine):
    """Migrate a clean schema for CRUD tests, then yield a TestClient."""
    from alembic import command
    from alembic.config import Config

    # Reset public schema so CRUD tests own their data.
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    alembic_ini = API_ROOT / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    os.environ["DATABASE_URL"] = engine.url.render_as_string(hide_password=False)
    command.upgrade(cfg, "head")

    # Rebuild app modules against the test DATABASE_URL.
    import importlib

    import app.config as config_mod
    import app.db as db_mod

    config_mod.get_settings.cache_clear()
    importlib.reload(config_mod)
    importlib.reload(db_mod)
    import app.main as main_mod

    importlib.reload(main_mod)

    with TestClient(main_mod.app) as client:
        yield client


def test_health(api_client: TestClient) -> None:
    res = api_client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_zone_crud_soft_delete_restore_include_inactive(api_client: TestClient) -> None:
    # Create zone
    created = api_client.post("/api/v1/zones", json={"name": "TestZone", "description": "d"})
    assert created.status_code == 201, created.text
    zone = created.json()
    zone_id = zone["id"]
    assert zone["is_active"] is True

    # Nested department + category + subcategory
    dept = api_client.post(
        f"/api/v1/zones/{zone_id}/departments",
        json={"name": "DeptA"},
    ).json()
    cat = api_client.post(
        f"/api/v1/departments/{dept['id']}/categories",
        json={"name": "CatA"},
    ).json()
    sub = api_client.post(
        f"/api/v1/categories/{cat['id']}/subcategories",
        json={"name": "SubA"},
    ).json()

    # Soft-delete zone cascades
    deleted = api_client.delete(f"/api/v1/zones/{zone_id}")
    assert deleted.status_code == 204
    assert api_client.delete(f"/api/v1/zones/{zone_id}").status_code == 204  # idempotent

    active_list = api_client.get("/api/v1/zones")
    assert active_list.status_code == 200
    assert all(item["id"] != zone_id for item in active_list.json()["items"])

    inactive_list = api_client.get("/api/v1/zones", params={"include_inactive": True})
    ids = {item["id"] for item in inactive_list.json()["items"]}
    assert zone_id in ids

    got = api_client.get(f"/api/v1/zones/{zone_id}")
    assert got.status_code == 200
    assert got.json()["is_active"] is False

    for path in (
        f"/api/v1/departments/{dept['id']}",
        f"/api/v1/categories/{cat['id']}",
        f"/api/v1/subcategories/{sub['id']}",
    ):
        assert api_client.get(path).json()["is_active"] is False

    # Restore node-only: zone restores, children stay inactive
    restored = api_client.post(f"/api/v1/zones/{zone_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["is_active"] is True
    assert api_client.get(f"/api/v1/departments/{dept['id']}").json()["is_active"] is False

    # Child restore with inactive parent → 409
    conflict = api_client.post(f"/api/v1/categories/{cat['id']}/restore")
    assert conflict.status_code == 409
    assert conflict.headers["content-type"].startswith("application/problem+json")

    # Restore chain
    assert api_client.post(f"/api/v1/departments/{dept['id']}/restore").status_code == 200
    assert api_client.post(f"/api/v1/categories/{cat['id']}/restore").status_code == 200
    assert api_client.post(f"/api/v1/subcategories/{sub['id']}/restore").status_code == 200

    # Duplicate name (active or inactive) → 409
    other = api_client.post("/api/v1/zones", json={"name": "OtherZone"}).json()
    api_client.delete(f"/api/v1/zones/{other['id']}")
    dup = api_client.post("/api/v1/zones", json={"name": "OtherZone"})
    assert dup.status_code == 409

    missing = api_client.get(f"/api/v1/zones/{uuid.uuid4()}")
    assert missing.status_code == 404
    assert missing.headers["content-type"].startswith("application/problem+json")


def test_taxonomy_tree_and_paths(api_client: TestClient) -> None:
    zone = api_client.post("/api/v1/zones", json={"name": "TreeZone"}).json()
    dept = api_client.post(
        f"/api/v1/zones/{zone['id']}/departments", json={"name": "TreeDept"}
    ).json()
    cat = api_client.post(
        f"/api/v1/departments/{dept['id']}/categories", json={"name": "TreeCat"}
    ).json()
    api_client.post(
        f"/api/v1/categories/{cat['id']}/subcategories", json={"name": "TreeSub"}
    )

    tree = api_client.get("/api/v1/taxonomy/tree")
    assert tree.status_code == 200
    names = {z["name"] for z in tree.json()["items"]}
    assert "TreeZone" in names

    paths = api_client.get("/api/v1/taxonomy/paths")
    assert paths.status_code == 200
    full_paths = {p["full_path"] for p in paths.json()["items"]}
    assert "TreeZone > TreeDept > TreeCat > TreeSub" in full_paths
