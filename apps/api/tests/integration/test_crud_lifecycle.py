import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def suffix():
    return uuid.uuid4().hex[:8]


def test_health_and_ready():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_full_lifecycle_soft_delete_restore(suffix):
    # Create a fresh subtree.
    zone = client.post("/api/v1/zones", json={"name": f"Z-{suffix}"}).json()
    zid = zone["id"]
    assert zone["is_active"] is True

    # Duplicate sibling -> 409.
    dup = client.post("/api/v1/zones", json={"name": f"Z-{suffix}"})
    assert dup.status_code == 409

    dept = client.post(f"/api/v1/zones/{zid}/departments", json={"name": "D1"}).json()
    cat = client.post(f"/api/v1/departments/{dept['id']}/categories", json={"name": "C1"}).json()
    sub = client.post(f"/api/v1/categories/{cat['id']}/subcategories", json={"name": "S1"}).json()

    # Update (PUT).
    updated = client.put(
        f"/api/v1/departments/{dept['id']}", json={"name": "D1", "description": "changed"}
    ).json()
    assert updated["description"] == "changed"

    # Soft-delete cascades to descendants.
    assert client.delete(f"/api/v1/zones/{zid}").status_code == 204
    assert client.get(f"/api/v1/subcategories/{sub['id']}").json()["is_active"] is False
    # Idempotent.
    assert client.delete(f"/api/v1/zones/{zid}").status_code == 204

    # Active-only list excludes retired zone; include_inactive returns it.
    active = client.get("/api/v1/zones").json()["items"]
    assert all(z["id"] != zid for z in active)
    withinactive = client.get("/api/v1/zones?include_inactive=true").json()["items"]
    assert any(z["id"] == zid for z in withinactive)

    # Restoring child while parent inactive -> 409.
    assert client.post(f"/api/v1/subcategories/{sub['id']}/restore").status_code == 409

    # Restore top-down.
    assert client.post(f"/api/v1/zones/{zid}/restore").status_code == 200
    client.post(f"/api/v1/departments/{dept['id']}/restore")
    client.post(f"/api/v1/categories/{cat['id']}/restore")
    restored = client.post(f"/api/v1/subcategories/{sub['id']}/restore").json()
    assert restored["is_active"] is True

    # 404 for unknown id.
    assert client.get(f"/api/v1/zones/{uuid.uuid4()}").status_code == 404

    # Cleanup (retire the temp subtree so it doesn't clutter active views).
    client.delete(f"/api/v1/zones/{zid}")


def test_seed_paths_present():
    paths = client.get("/api/v1/taxonomy/paths").json()["items"]
    assert len(paths) >= 61
    full = {p["full_path"] for p in paths}
    assert "Perimeter > Bakery > Breakfast Bakery > Refrigerated English Muffins and Biscuits" in full
