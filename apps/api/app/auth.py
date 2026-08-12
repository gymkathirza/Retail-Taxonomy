"""Authentication for /api/v1/*.

Accepts EITHER HTTP Basic Auth (demo credentials) OR an OAuth2/OIDC Bearer
access token (Phase 2). Basic Auth is always available; Bearer is accepted
only when OIDC is configured. `require_basic_auth` is retained for
backward compatibility.
"""

from __future__ import annotations

import base64
import binascii
import secrets
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app import config, oidc

security = HTTPBasic(auto_error=False)

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass
class Principal:
    """The authenticated caller for a request."""

    sub: str
    method: str  # "basic" | "oidc"
    scopes: list[str] = field(default_factory=list)


def _unauthorized(detail: str, schemes: str = "Basic, Bearer") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": schemes},
    )


def _basic_ok(username: str, password: str) -> bool:
    settings = config.get_settings()
    user_ok = secrets.compare_digest(username, settings.demo_user)
    pass_ok = secrets.compare_digest(password, settings.demo_password)
    return user_ok and pass_ok


def require_basic_auth(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security),
) -> str:
    """HTTP Basic Auth dependency (retained for backward compatibility)."""
    if credentials is None:
        raise _unauthorized("Authentication required", schemes="Basic")
    if not _basic_ok(credentials.username, credentials.password):
        raise _unauthorized("Invalid credentials", schemes="Basic")
    request.state.user = credentials.username
    return credentials.username


def _authenticate(request: Request) -> Principal:
    header = request.headers.get("Authorization")
    if not header:
        raise _unauthorized("Authentication required")

    scheme, _, param = header.partition(" ")
    scheme = scheme.lower().strip()
    param = param.strip()

    if scheme == "basic":
        try:
            username, _, password = base64.b64decode(param).decode("utf-8").partition(":")
        except (binascii.Error, ValueError, UnicodeDecodeError):
            raise _unauthorized("Invalid Basic credentials")
        if not _basic_ok(username, password):
            raise _unauthorized("Invalid credentials")
        request.state.user = username
        return Principal(sub=username, method="basic")

    if scheme == "bearer":
        if not oidc.is_oidc_enabled():
            raise _unauthorized("Bearer tokens are not accepted (OIDC not configured)")
        try:
            claims = oidc.verify_bearer_token(param)
        except oidc.OIDCError as exc:
            raise _unauthorized(f"Invalid token: {exc}", schemes="Bearer")
        sub = str(claims.get("preferred_username") or claims.get("sub") or "unknown")
        request.state.user = sub
        return Principal(sub=sub, method="oidc", scopes=oidc.extract_scopes(claims))

    raise _unauthorized("Unsupported authorization scheme")


def require_auth(request: Request) -> Principal:
    """Unified auth: accept Basic or Bearer, then enforce optional write scope.

    When `OIDC_REQUIRED_SCOPE` is set, OIDC principals must carry that scope to
    perform mutating requests (POST/PUT/PATCH/DELETE). Basic principals (demo)
    remain fully authorized, preserving current behavior.
    """
    principal = _authenticate(request)

    required = config.get_settings().oidc_required_scope
    if (
        required
        and principal.method == "oidc"
        and request.method.upper() in _WRITE_METHODS
        and required not in principal.scopes
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required scope '{required}'",
        )
    return principal
