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


def test_unauthorized_offers_both_schemes(auth_client: TestClient) -> None:
    res = auth_client.get("/api/v1/zones")
    assert res.status_code == 401
    www = res.headers.get("WWW-Authenticate", "")
    assert "Basic" in www and "Bearer" in www


# ---------------------------------------------------------------------------
# OIDC (Bearer) coexistence — tokens signed locally, JWKS monkeypatched.
# ---------------------------------------------------------------------------

_KID = "it-key-1"
_ISSUER = "https://issuer.test/realms/retail"
_AUDIENCE = "retail-taxonomy-api"


@pytest.fixture
def oidc_enabled(monkeypatch):
    import time

    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    from app import oidc
    from app.config import get_settings

    keypair = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    monkeypatch.setenv("OIDC_ISSUER", _ISSUER)
    monkeypatch.setenv("OIDC_AUDIENCE", _AUDIENCE)
    get_settings.cache_clear()
    oidc.reset_cache()
    monkeypatch.setattr(oidc, "_load_keys", lambda force=False: {_KID: keypair.public_key()})

    def mint(scope: str = "openid taxonomy.read taxonomy.write") -> str:
        now = int(time.time())
        claims = {
            "iss": _ISSUER,
            "aud": _AUDIENCE,
            "sub": "svc-1",
            "preferred_username": "svc.user",
            "iat": now,
            "exp": now + 300,
            "scope": scope,
        }
        return jwt.encode(claims, keypair, algorithm="RS256", headers={"kid": _KID})

    yield mint
    get_settings.cache_clear()
    oidc.reset_cache()


def test_api_accepts_bearer_token(auth_client: TestClient, oidc_enabled) -> None:
    token = oidc_enabled()
    res = auth_client.get("/api/v1/zones", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    # Basic still works while OIDC is enabled (coexistence).
    assert auth_client.get("/api/v1/zones", auth=("admin", "password")).status_code == 200


def test_api_rejects_invalid_bearer(auth_client: TestClient, oidc_enabled) -> None:
    token = oidc_enabled() + "tampered"
    res = auth_client.get("/api/v1/zones", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_write_scope_enforced_for_oidc(auth_client: TestClient, oidc_enabled, monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("OIDC_REQUIRED_SCOPE", "taxonomy.write")
    get_settings.cache_clear()

    read_only = oidc_enabled(scope="openid taxonomy.read")
    writer = oidc_enabled(scope="openid taxonomy.read taxonomy.write")

    # Read allowed with a read-only token.
    assert auth_client.get(
        "/api/v1/zones", headers={"Authorization": f"Bearer {read_only}"}
    ).status_code == 200
    # Write rejected (403) without the required scope.
    assert auth_client.post(
        "/api/v1/zones",
        json={"name": "ScopeTestZone"},
        headers={"Authorization": f"Bearer {read_only}"},
    ).status_code == 403
    # Write allowed with the required scope.
    assert auth_client.post(
        "/api/v1/zones",
        json={"name": "ScopeTestZoneOK"},
        headers={"Authorization": f"Bearer {writer}"},
    ).status_code == 201
    # Basic principals remain fully authorized regardless of scope config.
    assert auth_client.post(
        "/api/v1/zones",
        json={"name": "ScopeTestZoneBasic"},
        auth=("admin", "password"),
    ).status_code == 201
