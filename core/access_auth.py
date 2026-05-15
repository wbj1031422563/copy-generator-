"""Optional HTTP session login (env: COPYGEN_AUTH_USER / COPYGEN_AUTH_PASSWORD)."""

from __future__ import annotations

import hashlib
import os
import secrets
from typing import Final

SESSION_KEY: Final = "copygen_auth"
PUBLIC_API_PREFIXES: Final = (
    "/api/auth/login",
    "/api/auth/status",
    "/api/auth/logout",
    "/api/health",
)


def auth_enabled() -> bool:
    return bool(_password())


def username() -> str:
    return (os.environ.get("COPYGEN_AUTH_USER") or "admin").strip() or "admin"


def _password() -> str:
    return (os.environ.get("COPYGEN_AUTH_PASSWORD") or "").strip()


def session_secret() -> str:
    explicit = (os.environ.get("COPYGEN_AUTH_SECRET") or "").strip()
    if explicit:
        return explicit
    pwd = _password()
    if pwd:
        return hashlib.sha256(f"copygen-session:{pwd}".encode()).hexdigest()
    return "copygen-dev-insecure-change-me"


def verify_credentials(user: str, password: str) -> bool:
    if not auth_enabled():
        return True
    if not secrets.compare_digest((user or "").strip(), username()):
        return False
    return secrets.compare_digest(password or "", _password())


def is_public_path(path: str) -> bool:
    if path.startswith("/assets/"):
        return True
    if path in ("/", "/login", "/favicon.ico"):
        return True
    return any(
        path == p or path.startswith(p + "/")
        for p in PUBLIC_API_PREFIXES
    )


def is_authenticated(session: dict) -> bool:
    if not auth_enabled():
        return True
    return bool(session.get(SESSION_KEY))
