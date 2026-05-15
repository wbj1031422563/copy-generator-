"""HTTP auth endpoints."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from web.server import app  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("COPYGEN_AUTH_USER", "tester")
    monkeypatch.setenv("COPYGEN_AUTH_PASSWORD", "pass1234")
    with TestClient(app) as c:
        yield c


def test_login_protects_api(client):
    r = client.get("/api/stats")
    assert r.status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"username": "tester", "password": "pass1234"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["username"] == "tester"

    r2 = client.get("/api/stats")
    assert r2.status_code == 200


def test_wrong_password(client):
    r = client.post(
        "/api/auth/login",
        json={"username": "tester", "password": "wrong"},
    )
    assert r.status_code == 401
