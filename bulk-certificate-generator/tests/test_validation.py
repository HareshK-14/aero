import pytest


def test_empty_recipients_rejected(client):
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 422


def test_invalid_email_rejected(client):
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [{"name": "Test User", "email": "not-an-email"}],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 422


def test_missing_event_name_rejected(client):
    body = {
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 422


def test_missing_certificate_title_rejected(client):
    body = {
        "event_name": "Test Event",
        "issue_date": "2026-01-01",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 422


def test_invalid_date_rejected(client):
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Cert",
        "issue_date": "not-a-date",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 422


def test_missing_recipient_name_rejected(client):
    body = {
        "event_name": "Test Event",
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [{"email": "test@example.com"}],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 422


def test_empty_event_name_rejected(client):
    body = {
        "event_name": "   ",
        "certificate_title": "Test Cert",
        "issue_date": "2026-01-01",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/v1/certificates/jobs", json=body)
    assert response.status_code == 422
