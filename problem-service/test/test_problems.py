"""Integration tests: run inside the problem-service container against the compose Postgres.
RabbitMQ publishing is mocked here; the real queue is checked manually (see README / phase notes).

    docker compose exec problem-service pytest -q /service/test
"""
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from main import app
from services import queue_publisher

SERVICE_HEADERS = {"X-Service-Token": os.environ["SERVICE_TOKEN"]}

PROBLEM = {
    "title": "Add Two Numbers",
    "difficulty": "easy",
    "description": "Read A and B, print A + B.",
    "constraints": ["-10^6 <= A, B <= 10^6"],
    "examples": [{"input": "2 3", "output": "5", "explanation": "2 + 3 = 5"}],
    "sample_testcases": [{"input": "1 2", "output": "3"}],
    "hidden_testcases": [{"input": "5 5", "output": "10"}],
    "topics": ["Math", " math ", "Implementation"],
    "starter_code": {"python": "print(sum(map(int, input().split())))"},
}


def make_token(role="user", user_id=None):
    """Mint an access token the same way auth-service does (shared JWT_SECRET_KEY)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "test@example.com",
        "user_id": user_id or str(uuid4()),
        "role": role,
        "is_verified": True,
        "is_active": True,
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, os.environ["JWT_SECRET_KEY"], algorithm=os.getenv("JWT_ALGORITHM", "HS256"))


def auth(role="user", user_id=None):
    return {"Authorization": f"Bearer {make_token(role, user_id)}"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def published(monkeypatch):
    messages = []
    monkeypatch.setattr(queue_publisher, "publish_submission", messages.append)
    return messages


@pytest.fixture
def problem_id(client):
    r = client.post("/api/v1/problems", json=PROBLEM, headers=auth("admin"))
    assert r.status_code == 201, r.text
    yield r.json()["problem_id"]
    # Clean up (submissions are removed by ON DELETE CASCADE); 404 if the test already deleted it
    client.delete(f"/api/v1/problems/{r.json()['problem_id']}", headers=auth("admin"))


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_create_requires_admin(client):
    assert client.post("/api/v1/problems", json=PROBLEM).status_code == 401
    assert client.post("/api/v1/problems", json=PROBLEM, headers=auth("user")).status_code == 403


def test_problem_crud(client, problem_id):
    r = client.get(f"/api/v1/problems/{problem_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["topics"] == ["implementation", "math"]  # normalized
    assert "hidden_testcases" not in body                 # never exposed publicly

    updated = PROBLEM | {"title": "Add Two Integers", "difficulty": "medium"}
    r = client.put(f"/api/v1/problems/{problem_id}", json=updated, headers=auth("admin"))
    assert r.status_code == 200
    assert r.json()["title"] == "Add Two Integers"

    assert client.get("/api/v1/problems").json()["total"] >= 1

    assert client.delete(f"/api/v1/problems/{problem_id}", headers=auth("admin")).status_code == 204
    assert client.get(f"/api/v1/problems/{problem_id}").status_code == 404


def test_create_validates_body(client):
    bad = PROBLEM | {"difficulty": "impossible", "hidden_testcases": []}
    assert client.post("/api/v1/problems", json=bad, headers=auth("admin")).status_code == 422


def test_submission_is_queued_and_published(client, problem_id, published):
    user_id = str(uuid4())
    r = client.post(
        "/api/v1/submissions",
        json={"problem_id": problem_id, "language": "python", "source_code": "print(1)"},
        headers=auth(user_id=user_id),
    )
    assert r.status_code == 202
    submission_id = r.json()["submission_id"]
    assert r.json()["status"] == "queued"
    assert published == [{
        "submission_id": submission_id,
        "problem_id": problem_id,
        "language": "python",
        "source_code": "print(1)",
    }]

    r = client.get(f"/api/v1/submissions/{submission_id}", headers=auth(user_id=user_id))
    assert r.status_code == 200
    assert r.json()["status"] == "queued"

    # Another user cannot see it
    assert client.get(f"/api/v1/submissions/{submission_id}", headers=auth()).status_code == 404


def test_submission_errors(client, problem_id, published):
    body = {"problem_id": problem_id, "language": "python", "source_code": "print(1)"}
    assert client.post("/api/v1/submissions", json=body).status_code == 401
    assert client.post("/api/v1/submissions", json=body | {"language": "ruby"}, headers=auth()).status_code == 422
    assert client.post("/api/v1/submissions", json=body | {"problem_id": 999999999}, headers=auth()).status_code == 404
    assert published == []


def test_internal_testcases_and_result(client, problem_id, published):
    assert client.get(f"/internal/problems/{problem_id}/testcases").status_code == 401

    r = client.get(f"/internal/problems/{problem_id}/testcases", headers=SERVICE_HEADERS)
    assert r.status_code == 200
    assert r.json()["testcases"] == PROBLEM["sample_testcases"] + PROBLEM["hidden_testcases"]

    user_id = str(uuid4())
    submission_id = client.post(
        "/api/v1/submissions",
        json={"problem_id": problem_id, "language": "python", "source_code": "print(3)"},
        headers=auth(user_id=user_id),
    ).json()["submission_id"]

    result = {"status": "completed", "verdict": "Accepted", "passed_count": 2, "total_count": 2,
              "runtime_ms": 12, "memory_kb": 3400, "error_output": None}
    r = client.put(f"/internal/submissions/{submission_id}/result", json=result, headers=SERVICE_HEADERS)
    assert r.status_code == 204

    r = client.get(f"/api/v1/submissions/{submission_id}", headers=auth(user_id=user_id))
    assert r.json()["verdict"] == "Accepted"
    assert r.json()["runtime_ms"] == 12
