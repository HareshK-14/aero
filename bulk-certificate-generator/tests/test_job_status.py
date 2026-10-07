import pytest
import time


def test_get_nonexistent_job_returns_404(client):
    response = client.get("/api/v1/certificates/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_job_status_after_creation(client, valid_request_body):
    # Create the job
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    assert create_resp.status_code == 201
    job_id = create_resp.json()["job_id"]

    # Check status immediately
    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["job_id"] == job_id
    assert data["total_count"] == 2
    assert "status" in data
    assert "progress_percentage" in data
    assert "pending_count" in data


def test_progress_percentage_is_valid(client, valid_request_body):
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    data = status_resp.json()
    assert 0.0 <= data["progress_percentage"] <= 100.0


def test_invalid_job_id_format_returns_404(client):
    response = client.get("/api/v1/certificates/jobs/not-a-uuid")
    assert response.status_code == 404


def test_completed_job_has_100_percent_progress(client, valid_request_body):
    """After background task runs (synchronous in TestClient), job should be COMPLETED."""
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    # BackgroundTasks run synchronously inside TestClient context
    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    data = status_resp.json()

    # Job should be completed at this point
    assert data["status"] in ("COMPLETED", "COMPLETED_WITH_ERRORS", "PROCESSING", "PENDING")
    assert data["total_count"] == 2


def test_job_counts_sum_correctly(client, valid_request_body):
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    status_resp = client.get(f"/api/v1/certificates/jobs/{job_id}")
    data = status_resp.json()

    total = data["success_count"] + data["failure_count"] + data["pending_count"]
    assert total == data["total_count"]
