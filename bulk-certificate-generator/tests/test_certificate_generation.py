import pytest
import os
from datetime import date
from pathlib import Path
from app.services.certificate_service import generate_certificate
from app.config import settings

# A fixed test certificate ID for cleanup
TEST_CERT_ID = "test-cert-00000001"


@pytest.fixture(autouse=True)
def cleanup_test_cert():
    """Clean up any generated test PDF after each test."""
    yield
    test_file = Path(settings.certificate_storage_path) / f"certificate_{TEST_CERT_ID}.pdf"
    if test_file.exists():
        test_file.unlink()


def test_generate_certificate_creates_file():
    path = generate_certificate(
        recipient_name="Haresh K",
        event_name="AI Workshop 2026",
        certificate_title="Certificate of Participation",
        issue_date=date(2026, 10, 7),
        certificate_id=TEST_CERT_ID,
    )
    assert Path(path).exists()
    assert path.endswith(".pdf")


def test_generate_certificate_file_not_empty():
    path = generate_certificate(
        recipient_name="Rahul Kumar",
        event_name="Python Bootcamp",
        certificate_title="Certificate of Completion",
        issue_date=date(2026, 6, 15),
        certificate_id=TEST_CERT_ID,
    )
    assert os.path.getsize(path) > 0


def test_generate_certificate_returns_string():
    result = generate_certificate(
        recipient_name="Priya S",
        event_name="Data Science Summit",
        certificate_title="Participation Award",
        issue_date=date(2026, 3, 1),
        certificate_id=TEST_CERT_ID,
    )
    assert isinstance(result, str)


def test_generate_certificate_with_special_characters_in_name():
    """Ensure names with special characters don't crash PDF generation."""
    path = generate_certificate(
        recipient_name="Dr. Müller-García",
        event_name="International Summit",
        certificate_title="Certificate of Excellence",
        issue_date=date(2026, 1, 1),
        certificate_id=TEST_CERT_ID,
    )
    assert Path(path).exists()
    assert os.path.getsize(path) > 0
