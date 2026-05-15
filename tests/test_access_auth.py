"""Access auth helpers."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import access_auth


def test_disabled_without_password(monkeypatch):
    monkeypatch.delenv("COPYGEN_AUTH_PASSWORD", raising=False)
    assert access_auth.auth_enabled() is False
    assert access_auth.verify_credentials("any", "any") is True


def test_enabled_with_password(monkeypatch):
    monkeypatch.setenv("COPYGEN_AUTH_USER", "demo")
    monkeypatch.setenv("COPYGEN_AUTH_PASSWORD", "secret-pass")
    assert access_auth.auth_enabled() is True
    assert access_auth.verify_credentials("demo", "secret-pass") is True
    assert access_auth.verify_credentials("demo", "wrong") is False
    assert access_auth.verify_credentials("other", "secret-pass") is False


def test_public_paths():
    assert access_auth.is_public_path("/api/auth/login")
    assert access_auth.is_public_path("/api/health")
    assert access_auth.is_public_path("/assets/index.js")
    assert not access_auth.is_public_path("/api/generate")
