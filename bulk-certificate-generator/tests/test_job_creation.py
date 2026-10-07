import pytest
from fastapi.testclient import TestClient


def test_create_job_returns_201(client, valid_request_body):
    response = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    assert response.status_code == 201


def test_create_job_response_fields(client, valid_request_body):
    response = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["total_count"] == 2
    assert data["success_count"] == 0
    assert data["failure_count"] == 0


def test_create_job_with_single_recipient(client):
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Certificate",
        "issue_date": "2026-01-01",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 201
    assert response.json()["total_count"] == 1


def test_create_job_with_multiple_recipients(client):
    recipients = [{"name": f"User {i}", "email": f"user{i}@example.com"} for i in range(10)]
    body = {
        "event_name": "Big Event",
        "certificate_title": "Award",
        "issue_date": "2026-06-15",
        "recipients": recipients,
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 201
    assert response.json()["total_count"] == 10
