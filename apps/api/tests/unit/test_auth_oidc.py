"""Unit tests for OIDC Bearer-token verification (Phase 2).

Tokens are signed locally with a throwaway RSA keypair; the JWKS lookup is
monkeypatched so no network/IdP is required.
"""

from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app import oidc

KID = "test-key-1"
ISSUER = "https://issuer.test/realms/retail"
AUDIENCE = "retail-taxonomy-api"


@pytest.fixture
def keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def configure_oidc(monkeypatch, keypair):
    monkeypatch.setenv("OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.delenv("OIDC_JWKS_URL", raising=False)
    monkeypatch.delenv("OIDC_REQUIRED_SCOPE", raising=False)

    from app.config import get_settings

    get_settings.cache_clear()
    oidc.reset_cache()
    monkeypatch.setattr(oidc, "_load_keys", lambda force=False: {KID: keypair.public_key()})
    yield
    get_settings.cache_clear()
    oidc.reset_cache()


def _make_token(keypair, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "user-123",
        "preferred_username": "sso.user",
        "iat": now,
        "exp": now + 300,
        "scope": "openid taxonomy.read",
    }
    claims.update(overrides)
    kid = overrides.pop("_kid", KID)
    return jwt.encode(claims, keypair, algorithm="RS256", headers={"kid": kid})


def test_valid_token_returns_claims(configure_oidc, keypair):
    token = _make_token(keypair)
    claims = oidc.verify_bearer_token(token)
    assert claims["sub"] == "user-123"
    assert claims["preferred_username"] == "sso.user"


def test_expired_token_rejected(configure_oidc, keypair):
    # Expire well beyond the configured clock-skew leeway (30s).
    token = _make_token(keypair, exp=int(time.time()) - 120, iat=int(time.time()) - 300)
    with pytest.raises(oidc.OIDCError):
        oidc.verify_bearer_token(token)


def test_wrong_audience_rejected(configure_oidc, keypair):
    token = _make_token(keypair, aud="some-other-api")
    with pytest.raises(oidc.OIDCError):
        oidc.verify_bearer_token(token)


def test_wrong_issuer_rejected(configure_oidc, keypair):
    token = _make_token(keypair, iss="https://evil.test/")
    with pytest.raises(oidc.OIDCError):
        oidc.verify_bearer_token(token)


def test_bad_signature_rejected(configure_oidc):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _make_token(other_key)  # signed by a key the JWKS doesn't contain
    with pytest.raises(oidc.OIDCError):
        oidc.verify_bearer_token(token)


def test_unknown_kid_rejected(monkeypatch, configure_oidc, keypair):
    monkeypatch.setattr(oidc, "_load_keys", lambda force=False: {})
    token = _make_token(keypair)
    with pytest.raises(oidc.OIDCError):
        oidc.verify_bearer_token(token)


def test_disabled_when_unconfigured(monkeypatch):
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    monkeypatch.delenv("OIDC_JWKS_URL", raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    assert oidc.is_oidc_enabled() is False
    with pytest.raises(oidc.OIDCError):
        oidc.verify_bearer_token("anything")
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "claims,expected",
    [
        ({"scope": "openid taxonomy.read taxonomy.write"}, ["openid", "taxonomy.read", "taxonomy.write"]),
        ({"scp": ["a", "b"]}, ["a", "b"]),
        ({}, []),
    ],
)
def test_extract_scopes(claims, expected):
    assert oidc.extract_scopes(claims) == expected
