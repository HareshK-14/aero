import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.database import Base, get_db
from unittest.mock import patch

# Use SQLite for tests — no PostgreSQL needed
TEST_DATABASE_URL = "sqlite:///./test_certificates.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh SQLite database for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Test client with:
    - Overridden DB dependency (uses SQLite test session for API routes)
    - Patched SessionLocal in job_service (so background tasks also use SQLite)

    This is critical: FastAPI BackgroundTasks run synchronously inside the
    TestClient context, but process_bulk_job() creates its own SessionLocal.
    We patch it so it uses our test session factory instead.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.services.job_service.SessionLocal", TestSessionLocal):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture
def valid_request_body():
    return {
        "event_name": "AI Workshop 2026",
        "certificate_title": "Certificate of Participation",
        "issue_date": "2026-10-07",
        "recipients": [
            {"name": "Haresh K", "email": "haresh@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"},
        ],
    }
