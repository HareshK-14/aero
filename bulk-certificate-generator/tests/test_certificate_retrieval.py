import pytest
import time


def test_list_certificates_for_nonexistent_job(client):
    response = client.get("/api/v1/certificates/jobs/00000000-0000-0000-0000-000000000000/certificates")
    assert response.status_code == 404


def test_list_certificates_returns_correct_count(client, valid_request_body):
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    list_resp = client.get(f"/api/v1/certificates/jobs/{job_id}/certificates")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["job_id"] == job_id
    assert len(data["certificates"]) == 2


def test_download_nonexistent_certificate(client):
    response = client.get("/api/v1/certificates/00000000-0000-0000-0000-000000000000/download")
    assert response.status_code == 404


def test_completed_certificate_has_download_url(client, valid_request_body):
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    list_resp = client.get(f"/api/v1/certificates/jobs/{job_id}/certificates")
    certs = list_resp.json()["certificates"]

    completed = [c for c in certs if c["status"] == "COMPLETED"]
    if completed:
        assert completed[0]["download_url"] is not None
        assert "/download" in completed[0]["download_url"]


def test_certificate_fields_present(client, valid_request_body):
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    list_resp = client.get(f"/api/v1/certificates/jobs/{job_id}/certificates")
    certs = list_resp.json()["certificates"]
    for cert in certs:
        assert "certificate_id" in cert
        assert "recipient_name" in cert
        assert "email" in cert
        assert "status" in cert


def test_list_certificates_job_id_matches(client, valid_request_body):
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    list_resp = client.get(f"/api/v1/certificates/jobs/{job_id}/certificates")
    data = list_resp.json()
    assert data["job_id"] == job_id


def test_download_returns_pdf_for_completed_certificate(client, valid_request_body):
    """If background task runs synchronously, we can download the generated PDF."""
    create_resp = client.post("/api/v1/certificates/jobs", json=valid_request_body)
    job_id = create_resp.json()["job_id"]

    list_resp = client.get(f"/api/v1/certificates/jobs/{job_id}/certificates")
    certs = list_resp.json()["certificates"]

    completed = [c for c in certs if c["status"] == "COMPLETED"]
    if completed:
        cert_id = completed[0]["certificate_id"]
        dl_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "application/pdf"
