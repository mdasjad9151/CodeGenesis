"""Contests, daily challenge, Redis cache and rate limits. ai-service is mocked; Postgres and Redis are real.

    docker compose exec problem-service pytest -q /service/test
"""
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from core import cache
from db.connection import Database
from main import app
from services import ai_client, queue_publisher, submission_service
from test_problems import PROBLEM, auth

SERVICE_HEADERS = {"X-Service-Token": os.environ["SERVICE_TOKEN"]}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def created(client):
    """Track problems/contests made by a test and delete them afterwards."""
    ids = {"problems": [], "contests": []}
    yield ids
    for problem_id in ids["problems"]:
        client.delete(f"/api/v1/problems/{problem_id}", headers=auth("admin"))
    with Database.get_engine().begin() as conn:
        for contest_id in ids["contests"]:
            conn.execute(text("DELETE FROM contests WHERE contest_id = :id"), {"id": contest_id})
    cache.delete(f"daily:{datetime.now(timezone.utc).date().isoformat()}")


@pytest.fixture(autouse=True)
def no_queue(monkeypatch):
    monkeypatch.setattr(queue_publisher, "publish_submission", lambda message: None)


def make_problem(client, created, topic, difficulty="easy"):
    r = client.post("/api/v1/problems", json=PROBLEM | {"topics": [topic], "difficulty": difficulty}, headers=auth("admin"))
    assert r.status_code == 201, r.text
    created["problems"].append(r.json()["problem_id"])
    return r.json()["problem_id"]


def unique_topic():
    return f"topic{uuid4().hex[:8]}"


def generate(client, created, user_id, **body):
    r = client.post("/api/v1/contests/generate", json=body, headers=auth(user_id=user_id))
    if r.status_code == 201:
        created["contests"].append(r.json()["contest_id"])
    return r


# --- contests --------------------------------------------------------------

def test_contest_reuses_existing_problems_without_ai(client, created, monkeypatch):
    topic = unique_topic()
    ids = {make_problem(client, created, topic) for _ in range(3)}
    make_problem(client, created, topic, difficulty="hard")  # wrong difficulty, must not be picked
    monkeypatch.setattr(ai_client, "generate_problem", lambda *a: pytest.fail("AI should not be called"))

    r = generate(client, created, str(uuid4()), topic=topic.upper(), difficulty="easy", num_questions=2)
    assert r.status_code == 201, r.text
    body = r.json()
    assert (body["reused_count"], body["generated_count"]) == (2, 0)
    assert {p["problem_id"] for p in body["problems"]} <= ids
    assert [p["position"] for p in body["problems"]] == [1, 2]
    assert body["topic"] == topic


def test_contest_asks_ai_for_missing_problems(client, created, monkeypatch):
    topic = unique_topic()
    make_problem(client, created, topic)
    asked = []

    def fake_generate(t, difficulty):
        asked.append((t, difficulty))
        return make_problem(client, created, t)  # ai-service would save it via /internal/problems

    monkeypatch.setattr(ai_client, "generate_problem", fake_generate)
    r = generate(client, created, str(uuid4()), topic=topic, difficulty="easy", num_questions=3)
    assert r.status_code == 201
    assert (r.json()["reused_count"], r.json()["generated_count"]) == (1, 2)
    assert asked == [(topic, "easy")] * 2


def test_contest_fails_when_nothing_available(client, created, monkeypatch):
    def broken(*args):
        raise RuntimeError("ai-service down")

    monkeypatch.setattr(ai_client, "generate_problem", broken)
    r = generate(client, created, str(uuid4()), topic=unique_topic(), difficulty="medium", num_questions=2)
    assert r.status_code == 502


def test_contest_validation(client):
    headers = auth()
    assert client.post("/api/v1/contests/generate", json={"topic": "arrays", "difficulty": "easy", "num_questions": 9},
                       headers=headers).status_code == 422
    assert client.post("/api/v1/contests/generate", json={"topic": "a; drop table", "difficulty": "easy"},
                       headers=headers).status_code == 422
    assert client.post("/api/v1/contests/generate", json={"topic": "arrays", "difficulty": "easy"}).status_code == 401
    assert client.get(f"/api/v1/contests/{uuid4()}", headers=headers).status_code == 404


def test_contest_score_tally(client, created, monkeypatch):
    topic = unique_topic()
    make_problem(client, created, topic)
    make_problem(client, created, topic)
    outsider = make_problem(client, created, unique_topic())
    alice, bob = str(uuid4()), str(uuid4())
    contest = generate(client, created, alice, topic=topic, difficulty="easy", num_questions=2).json()
    contest_id = contest["contest_id"]
    first, second = (p["problem_id"] for p in contest["problems"])

    def submit_and_judge(user_id, problem_id, verdict):
        r = client.post("/api/v1/submissions", headers=auth(user_id=user_id), json={
            "problem_id": problem_id, "language": "python", "source_code": "print(1)", "contest_id": contest_id})
        assert r.status_code == 202, r.text
        client.put(f"/internal/submissions/{r.json()['submission_id']}/result", headers=SERVICE_HEADERS,
                   json={"status": "completed", "verdict": verdict})

    submit_and_judge(alice, first, "Accepted")
    submit_and_judge(alice, first, "Accepted")      # same problem twice counts once
    submit_and_judge(alice, second, "Wrong Answer")
    submit_and_judge(bob, first, "Accepted")
    submit_and_judge(bob, second, "Accepted")

    r = client.post("/api/v1/submissions", headers=auth(user_id=alice), json={
        "problem_id": outsider, "language": "python", "source_code": "print(1)", "contest_id": contest_id})
    assert r.status_code == 400

    body = client.get(f"/api/v1/contests/{contest_id}", headers=auth(user_id=alice)).json()
    assert body["my_solved"] == 1
    assert [p["solved"] for p in body["problems"]] == [True, False]
    assert [(e["user_id"], e["solved"], e["rank"]) for e in body["leaderboard"]] == [(bob, 2, 1), (alice, 1, 2)]


# --- daily challenge -------------------------------------------------------

def test_daily_endpoint_and_cache_invalidation(client, created):
    today = datetime.now(timezone.utc).date().isoformat()
    easy = make_problem(client, created, "daily-test")
    hard = make_problem(client, created, "daily-test", difficulty="hard")

    r = client.put("/internal/daily", headers=SERVICE_HEADERS,
                   json={"challenge_date": today, "difficulty": "easy", "problem_id": easy, "topic": "daily-test"})
    assert r.status_code == 204
    r = client.get("/api/v1/daily")
    assert r.status_code == 200
    assert easy in [p["problem_id"] for p in r.json()["problems"]]
    assert cache.get_json(f"daily:{today}") is not None  # now cached

    client.put("/internal/daily", headers=SERVICE_HEADERS,
               json={"challenge_date": today, "difficulty": "hard", "problem_id": hard, "topic": "daily-test"})
    assert hard in [p["problem_id"] for p in client.get("/api/v1/daily").json()["problems"]]  # cache was cleared


# --- problem list cache ----------------------------------------------------

def test_problem_list_cache_is_invalidated_on_write(client, created):
    before = client.get("/api/v1/problems").json()["total"]
    assert client.get("/api/v1/problems").json()["total"] == before  # served from cache
    make_problem(client, created, unique_topic())
    assert client.get("/api/v1/problems").json()["total"] == before + 1


# --- rate limit ------------------------------------------------------------

def test_submission_rate_limit(client, created, monkeypatch):
    problem_id = make_problem(client, created, unique_topic())
    settings = submission_service.config.submission_config() | {"rate_limit_per_minute": 2}
    monkeypatch.setattr(submission_service.config, "submission_config", lambda: settings)
    headers = auth(user_id=str(uuid4()))
    body = {"problem_id": problem_id, "language": "python", "source_code": "print(1)"}

    codes = [client.post("/api/v1/submissions", json=body, headers=headers).status_code for _ in range(3)]
    assert codes == [202, 202, 429]
    # Other users are not affected
    assert client.post("/api/v1/submissions", json=body, headers=auth()).status_code == 202
