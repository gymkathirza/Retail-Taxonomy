"""OAuth2 / OIDC access-token verification (Phase 2).

Provider-agnostic: verifies RS256 JWTs against the provider's JWKS
(discovered from the issuer, or an explicit JWKS URL). Keys are cached by
`kid` and refreshed on an unknown `kid` to handle key rotation.

OIDC is optional: when it is not configured, `is_oidc_enabled()` is False and
the API only accepts HTTP Basic Auth (backward compatible).
"""

from __future__ import annotations

import json
import threading
import time

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm

from app import config

_JWKS_TTL_SECONDS = 3600
_lock = threading.Lock()
_cache: dict[str, object] = {"keys_by_kid": {}, "fetched_at": 0.0}


class OIDCError(Exception):
    """Raised when a Bearer token cannot be validated."""


def is_oidc_enabled() -> bool:
    return config.get_settings().oidc_enabled


def _discover_jwks_url() -> str:
    settings = config.get_settings()
    if settings.oidc_jwks_url:
        return settings.oidc_jwks_url
    if not settings.oidc_issuer:
        raise OIDCError("OIDC is not configured")
    well_known = settings.oidc_issuer.rstrip("/") + "/.well-known/openid-configuration"
    resp = httpx.get(well_known, timeout=5.0)
    resp.raise_for_status()
    jwks_uri = resp.json().get("jwks_uri")
    if not jwks_uri:
        raise OIDCError("Issuer discovery document missing 'jwks_uri'")
    return jwks_uri


def _fetch_jwks(url: str) -> dict:
    resp = httpx.get(url, timeout=5.0)
    resp.raise_for_status()
    return resp.json()


def _load_keys(force: bool = False) -> dict:
    now = time.time()
    with _lock:
        keys = _cache["keys_by_kid"]
        fetched_at = float(_cache["fetched_at"])  # type: ignore[arg-type]
        if not force and keys and (now - fetched_at) < _JWKS_TTL_SECONDS:
            return keys  # type: ignore[return-value]
        jwks = _fetch_jwks(_discover_jwks_url())
        loaded: dict[str, object] = {}
        for key in jwks.get("keys", []):
            kid = key.get("kid")
            if kid and key.get("kty") == "RSA":
                loaded[kid] = RSAAlgorithm.from_jwk(json.dumps(key))
        _cache["keys_by_kid"] = loaded
        _cache["fetched_at"] = now
        return loaded


def _signing_key(kid: str):
    keys = _load_keys()
    if kid not in keys:
        # Unknown kid -> provider may have rotated keys; refresh once.
        keys = _load_keys(force=True)
    if kid not in keys:
        raise OIDCError("No matching signing key for token 'kid'")
    return keys[kid]


def reset_cache() -> None:
    """Clear the JWKS cache (used by tests)."""
    with _lock:
        _cache["keys_by_kid"] = {}
        _cache["fetched_at"] = 0.0


def extract_scopes(claims: dict) -> list[str]:
    """Collect scopes from common claim shapes (`scope`, `scp`)."""
    scopes: list[str] = []
    scope = claims.get("scope")
    if isinstance(scope, str):
        scopes.extend(scope.split())
    elif isinstance(scope, list):
        scopes.extend(str(s) for s in scope)
    scp = claims.get("scp")
    if isinstance(scp, str):
        scopes.extend(scp.split())
    elif isinstance(scp, list):
        scopes.extend(str(s) for s in scp)
    return scopes


def verify_bearer_token(token: str) -> dict:
    """Verify an OIDC access token and return its claims, or raise OIDCError."""
    settings = config.get_settings()
    if not settings.oidc_enabled:
        raise OIDCError("OIDC is not configured")
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise OIDCError(f"Malformed token header: {exc}") from exc

    kid = header.get("kid")
    if not kid:
        raise OIDCError("Token header missing 'kid'")
    key = _signing_key(kid)

    decode_options = {"require": ["exp"], "verify_aud": bool(settings.oidc_audience)}
    try:
        claims = jwt.decode(
            token,
            key=key,
            algorithms=["RS256"],
            audience=settings.oidc_audience or None,
            issuer=settings.oidc_issuer or None,
            leeway=settings.oidc_clock_skew_s,
            options=decode_options,
        )
    except jwt.PyJWTError as exc:
        raise OIDCError(str(exc)) from exc
    return claims
