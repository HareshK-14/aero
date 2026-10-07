"""
Failure handling tests.

Key design: FastAPI's TestClient runs BackgroundTasks SYNCHRONOUSLY within
the `client.post(...)` call. So we patch `generate_certificate` while that
call is active. The conftest also patches `app.services.job_service.SessionLocal`
so `process_bulk_job` uses the test SQLite session rather than real PostgreSQL.
"""
import pytest
from unittest.mock import patch


def test_failed_recipient_does_not_stop_others(client):
    """
    One recipient (Bob) fails → Alice and Charlie still get processed.
    All 3 generate_certificate calls must be attempted.
    """
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
            {"name": "Charlie", "email": "charlie@example.com"},
        ],
    }

    call_count = {"n": 0}

    def mock_generate(recipient_name, event_name, certificate_title, issue_date, certificate_id):
        call_count["n"] += 1
        if recipient_name == "Bob":
            raise ValueError("Simulated failure for Bob")
        from app.services.certificate_service import generate_certificate as real_gen
        return real_gen(recipient_name, event_name, certificate_title, issue_date, certificate_id)

    with patch("app.services.job_service.generate_certificate", side_effect=mock_generate):
        create_resp = client.post("/api/v1/certificates/jobs", json=body)
        assert create_resp.status_code == 201
        job_id = create_resp.json()["job_id"]

    # All 3 recipients must have been attempted
    assert call_count["n"] == 3

    # Job should be COMPLETED_WITH_ERRORS (2 success, 1 failure)
    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    data = status_resp.json()
    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["success_count"] == 2
    assert data["failure_count"] == 1


def test_all_failures_marks_job_as_failed(client):
    """When every recipient fails, the job status should be FAILED."""
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [
            {"name": "Alice", "email": "alice@example.com"},
        ],
    }

    def mock_fail(*args, **kwargs):
        raise RuntimeError("Always fails")

    with patch("app.services.job_service.generate_certificate", side_effect=mock_fail):
        create_resp = client.post("/api/v1/certificates/jobs", json=body)
        job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    data = status_resp.json()
    assert data["status"] == "FAILED"
    assert data["failure_count"] == 1
    assert data["success_count"] == 0


def test_failed_recipient_stores_error_message(client):
    """Failed recipients must have their error_message stored."""
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [
            {"name": "ErrorUser", "email": "error@example.com"},
        ],
    }

    def mock_fail(*args, **kwargs):
        raise ValueError("Disk full error")

    with patch("app.services.job_service.generate_certificate", side_effect=mock_fail):
        create_resp = client.post("/api/v1/certificates/jobs", json=body)
        job_id = create_resp.json()["job_id"]

    list_resp = client.get(f"/api/v1/certificates/jobs/{job_id}/certificates")
    certs = list_resp.json()["certificates"]
    assert len(certs) == 1
    assert certs[0]["status"] == "FAILED"
    assert certs[0]["error"] is not None
    assert "Disk full error" in certs[0]["error"]


def test_mixed_success_and_failure(client):
    """5 recipients: 3 succeed, 2 fail → COMPLETED_WITH_ERRORS."""
    body = {
        "event_name": "Mixed Event",
        "certificate_title": "Mixed Cert",
        "issue_date": "2026-01-01",
        "recipients": [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(5)
        ],
    }

    fail_names = {"User1", "User3"}

    def selective_fail(recipient_name, event_name, certificate_title, issue_date, certificate_id):
        if recipient_name in fail_names:
            raise ValueError(f"Intentional failure for {recipient_name}")
        from app.services.certificate_service import generate_certificate as real_gen
        return real_gen(recipient_name, event_name, certificate_title, issue_date, certificate_id)

    with patch("app.services.job_service.generate_certificate", side_effect=selective_fail):
        create_resp = client.post("/api/v1/certificates/jobs", json=body)
        job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    data = status_resp.json()
    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["success_count"] == 3
    assert data["failure_count"] == 2
