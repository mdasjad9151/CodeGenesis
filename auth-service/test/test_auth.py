"""Integration tests: run inside the auth-service container against the compose Postgres.

    docker compose exec auth-service pytest -q /service/test
"""
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from core.security import create_token, decode_token
from main import app
from services.auth_service import AuthService

PASSWORD = "s3cret-pass"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sent_otps(monkeypatch):
    """Capture OTPs instead of printing them."""
    otps = {}
    monkeypatch.setattr(AuthService, "send_otp", lambda self, email, otp: otps.__setitem__(email, otp))
    return otps


def register_and_verify(client, sent_otps) -> str:
    email = f"user-{uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201
    r = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": sent_otps[email]})
    assert r.status_code == 200
    return email


def login(client, email, password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_duplicate_returns_409(client, sent_otps):
    email = f"dup-{uuid4().hex[:8]}@example.com"
    assert client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD}).status_code == 201
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 409


def test_login_requires_verification(client, sent_otps):
    email = f"unverified-{uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD})
    assert login(client, email).status_code == 403

    r = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": "000000"})
    assert r.status_code == 400


def test_login_and_me(client, sent_otps):
    email = register_and_verify(client, sent_otps)

    assert login(client, email, "wrong-password").status_code == 401

    r = login(client, email)
    assert r.status_code == 200
    tokens = r.json()
    assert tokens["token_type"] == "bearer"

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert r.json()["role"] == "user"

    # Missing token / refresh token used as access token are rejected
    assert client.get("/api/v1/auth/me").status_code == 401
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401


def test_login_with_oauth2_form(client, sent_otps):
    email = register_and_verify(client, sent_otps)
    r = client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD})
    assert r.status_code == 200


def test_refresh_rotates_token(client, sent_otps):
    email = register_and_verify(client, sent_otps)
    old_refresh = login(client, email).json()["refresh_token"]

    r = client.post("/api/v1/auth/refresh-token", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new_refresh = r.json()["refresh_token"]
    assert new_refresh != old_refresh

    # The old refresh token is revoked after rotation
    r = client.post("/api/v1/auth/refresh-token", json={"refresh_token": old_refresh})
    assert r.status_code == 401

    r = client.post("/api/v1/auth/refresh-token", json={"refresh_token": new_refresh})
    assert r.status_code == 200


def test_token_contains_role_and_type():
    user = {"id": uuid4(), "email": "a@example.com", "role": "admin", "is_verified": True, "is_active": True}
    token = create_token(user=user, token_type="access", expires_delta=timedelta(minutes=1))
    payload = decode_token(token)
    assert payload["role"] == "admin"
    assert payload["token_type"] == "access"
    assert payload["user_id"] == str(user["id"])
