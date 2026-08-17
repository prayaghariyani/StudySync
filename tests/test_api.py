"""
Basic smoke tests for the core API flows: register/login, and the
subject -> task lifecycle. Uses a temporary SQLite DB (via
DATABASE_URL env var, set before importing the app) so tests never
touch studysync.db.

Run with: pytest
"""
import os
import tempfile

# Point at a throwaway DB file BEFORE importing the app, since
# app/database/database.py reads DATABASE_URL at import time.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def _register_and_login():
    resp = client.post("/api/auth/register", json={
        "name": "Test Student", "email": "test@example.com", "password": "password123",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_me():
    headers = _register_and_login()
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_duplicate_registration_rejected():
    client.post("/api/auth/register", json={
        "name": "Dup", "email": "dup@example.com", "password": "password123",
    })
    resp = client.post("/api/auth/register", json={
        "name": "Dup2", "email": "dup@example.com", "password": "password123",
    })
    assert resp.status_code == 400


def test_semester_subject_task_flow():
    headers = _register_and_login()

    sem_resp = client.post("/api/semesters", headers=headers, json={
        "name": "Fall 2026", "start_date": "2026-08-01", "end_date": "2026-12-15",
    })
    assert sem_resp.status_code == 201
    semester_id = sem_resp.json()["id"]

    subj_resp = client.post("/api/subjects", headers=headers, json={
        "semester_id": semester_id, "name": "Operating Systems", "credits": 4,
    })
    assert subj_resp.status_code == 201
    subject_id = subj_resp.json()["id"]

    task_resp = client.post("/api/tasks", headers=headers, json={
        "subject_id": subject_id, "title": "Assignment 1",
        "due_date": "2026-09-01T10:00:00", "priority": "HIGH",
    })
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]
    assert task_resp.json()["priority_score"] > 0

    complete_resp = client.post(f"/api/tasks/{task_id}/complete", headers=headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"

    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.json()["xp"] >= 10


def test_unauthenticated_request_rejected():
    resp = client.get("/api/tasks")
    assert resp.status_code == 401
