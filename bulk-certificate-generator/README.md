# Bulk Certificate Generator API

A production-quality backend API that generates PDF certificates in bulk for events and courses. Built with FastAPI, PostgreSQL, SQLAlchemy, and ReportLab.

---

## Project Overview

Organizations often need to issue certificates to hundreds of participants after an event or course. Doing this manually is slow and error-prone.

This API solves that by accepting a single bulk request with a list of recipients, generating professional PDF certificates for each one in the background, and allowing clients to track progress and download individual certificates — all without requiring one API call per recipient.

---

## Features

- ✅ **Bulk certificate generation** — submit 1 to 1000+ recipients in a single API call
- ✅ **Background processing** — returns immediately; certificates are generated asynchronously
- ✅ **Individual failure isolation** — one failed certificate does not stop the rest
- ✅ **Job status tracking** — real-time progress with counts and percentage
- ✅ **PDF download** — download any generated certificate by ID
- ✅ **Input validation** — rejects invalid emails, empty fields, bad dates
- ✅ **Consistent error responses** — structured JSON errors for all failure cases
- ✅ **Path traversal protection** — safe file downloads, no arbitrary path access
- ✅ **Swagger UI** — interactive API documentation at `/docs`
- ✅ **Docker support** — runs with a single `docker compose up --build`
- ✅ **Automated tests** — 30+ tests covering all major flows

---

## Technology Stack

| Technology | Version | Why |
|---|---|---|
| **Python** | 3.12+ | Modern, type-safe, widely used in backend development |
| **FastAPI** | 0.115 | Async-ready, auto-generates OpenAPI docs, excellent performance |
| **PostgreSQL** | 16 | Reliable relational DB, supports UUIDs natively, production standard |
| **SQLAlchemy** | 2.x | Industry-standard ORM, type-safe with mapped columns, avoids raw SQL |
| **Pydantic v2** | 2.9 | Schema validation with clear error messages, tight FastAPI integration |
| **Alembic** | 1.13 | Database migration management, tracks schema changes over time |
| **ReportLab** | 4.2 | Mature, pure-Python PDF generation library |
| **Pytest** | 8.3 | Python's standard testing framework |
| **Uvicorn** | 0.30 | ASGI server for running FastAPI |

---

## Architecture

### Application Structure

```
bulk-certificate-generator/
├── app/
│   ├── main.py              ← FastAPI app + router registration
│   ├── config.py            ← Settings loaded from .env
│   ├── database/
│   │   └── database.py      ← Engine, session factory, Base class
│   ├── models/
│   │   ├── generation_job.py ← GenerationJob ORM model
│   │   └── recipient.py      ← Recipient ORM model
│   ├── schemas/
│   │   └── certificate.py    ← Pydantic request/response schemas
│   ├── api/routes/
│   │   └── certificates.py   ← All 4 API endpoints
│   ├── services/
│   │   ├── job_service.py    ← Business logic: create job, process bulk
│   │   └── certificate_service.py ← ReportLab PDF generation
│   └── utils/
│       └── file_utils.py     ← Safe path handling, filename sanitization
├── tests/                    ← Pytest test suite
├── alembic/                  ← Database migrations
└── generated_certificates/   ← PDF files stored here
```

### API Flow

```
Client
  │
  │  POST /api/v1/certificates/jobs
  ▼
FastAPI Route
  │  1. Validate request (Pydantic)
  │  2. Create GenerationJob in DB (status=PENDING)
  │  3. Create Recipient records in DB
  │  4. Register background task
  │  5. Return job_id immediately (201)
  │
  ▼
FastAPI BackgroundTasks (runs after response is sent)
  │  1. Mark job as PROCESSING
  │  2. For each recipient:
  │     a. Mark recipient PROCESSING
  │     b. Call generate_certificate()  ─── ReportLab creates PDF
  │     c. On success: mark COMPLETED, save file path
  │     d. On failure: mark FAILED, save error_message
  │     e. Continue to next recipient regardless
  │  3. Recalculate success/failure counts
  │  4. Mark job COMPLETED / COMPLETED_WITH_ERRORS / FAILED
```

### Database Schema

```
generation_jobs
────────────────────────────────────────
id              UUID (PK)
status          VARCHAR  PENDING → PROCESSING → COMPLETED
event_name      VARCHAR
certificate_title VARCHAR
issue_date      DATE
total_count     INTEGER
success_count   INTEGER
failure_count   INTEGER
created_at      TIMESTAMP
started_at      TIMESTAMP (nullable)
completed_at    TIMESTAMP (nullable)

recipients
────────────────────────────────────────
id                  UUID (PK)
job_id              UUID (FK → generation_jobs.id)
name                VARCHAR
email               VARCHAR
certificate_status  VARCHAR  PENDING → PROCESSING → COMPLETED/FAILED
certificate_path    VARCHAR (nullable)   ← path to PDF file
error_message       VARCHAR (nullable)   ← set if generation failed
created_at          TIMESTAMP
completed_at        TIMESTAMP (nullable)
```

### Background Processing

FastAPI's `BackgroundTasks` runs the certificate generation *after* the HTTP response is sent. This means:

- The client gets a `job_id` in ~10ms
- Certificate generation happens in the background
- The client polls `GET /jobs/{job_id}` to check progress
- No Redis or Celery needed for this scale

### Error Handling

- **Pydantic validation errors** → 422 Unprocessable Entity (automatic)
- **Not found** → 404 with `{"detail": "..."}` message
- **Individual certificate failure** → stored in `recipient.error_message`, job continues
- **Total job failure** → job marked as `FAILED`
- **Unexpected server error** → 500 with generic message (no stack traces leaked)

---

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- `git`

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd bulk-certificate-generator
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 5. Start PostgreSQL

Make sure PostgreSQL is running and the database exists:

```bash
psql -U postgres -c "CREATE DATABASE certificate_db;"
```

### 6. Run Alembic Migrations

```bash
alembic upgrade head
```

### 7. Start the API

```bash
uvicorn app.main:app --reload
```

API is now available at: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db` | PostgreSQL connection string |
| `CERTIFICATE_STORAGE_PATH` | `./generated_certificates` | Directory where PDF files are stored |
| `ORGANIZATION_NAME` | `Infosys` | Organization name printed on certificates |

**Never commit your `.env` file. Use `.env.example` as a template.**

---

## API Documentation

### API 1 — Create Generation Job

**`POST /api/v1/certificates/jobs`**

Submit a bulk certificate generation request.

**Request Body:**
```json
{
  "event_name": "AI Workshop 2026",
  "certificate_title": "Certificate of Participation",
  "issue_date": "2026-10-07",
  "recipients": [
    { "name": "Haresh K", "email": "haresh@example.com" },
    { "name": "Rahul Kumar", "email": "rahul@example.com" },
    { "name": "Priya S", "email": "priya@example.com" }
  ]
}
```

**Response `201 Created`:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "total_count": 3,
  "success_count": 0,
  "failure_count": 0
}
```

**Error Cases:**
- `422` — empty recipients, invalid email, missing fields, invalid date

---

### API 2 — Get Job Status

**`GET /api/v1/certificates/jobs/{job_id}`**

Poll job progress.

**Response `200 OK`:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING",
  "total_count": 100,
  "success_count": 72,
  "failure_count": 3,
  "pending_count": 25,
  "progress_percentage": 75.0
}
```

**Job Status Values:**
| Status | Meaning |
|---|---|
| `PENDING` | Job created, not started yet |
| `PROCESSING` | Certificates being generated |
| `COMPLETED` | All certificates generated successfully |
| `COMPLETED_WITH_ERRORS` | Some succeeded, some failed |
| `FAILED` | All certificates failed |

**Error Cases:**
- `404` — job not found

---

### API 3 — List Certificates

**`GET /api/v1/certificates/jobs/{job_id}/certificates`**

List all recipients and their certificate status.

**Response `200 OK`:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "certificates": [
    {
      "certificate_id": "abc123..",
      "recipient_name": "Haresh K",
      "email": "haresh@example.com",
      "status": "COMPLETED",
      "download_url": "/api/v1/certificates/abc123../download",
      "error": null
    },
    {
      "certificate_id": "def456..",
      "recipient_name": "Bad User",
      "email": "bad@example.com",
      "status": "FAILED",
      "download_url": null,
      "error": "ReportLab error: ..."
    }
  ]
}
```

**Error Cases:**
- `404` — job not found

---

### API 4 — Download Certificate

**`GET /api/v1/certificates/{certificate_id}/download`**

Download a generated PDF certificate.

**Response `200 OK`:** Binary PDF file with `Content-Type: application/pdf`

**Error Cases:**
- `404` — certificate not found or not yet generated
- `403` — path traversal attempt detected

---

## Running Tests

Tests use **SQLite** (in-memory style), so **PostgreSQL is NOT needed** to run tests.

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_failure_handling.py -v

# Run with coverage (if coverage installed)
pytest tests/ -v --tb=short
```

Expected output:
```
tests/test_job_creation.py::test_create_job_returns_201 PASSED
tests/test_job_creation.py::test_create_job_response_fields PASSED
tests/test_validation.py::test_empty_recipients_rejected PASSED
tests/test_validation.py::test_invalid_email_rejected PASSED
...
30+ tests, all PASSED
```

---

## Docker

### Run Everything with Docker Compose

```bash
docker compose up --build
```

This starts:
1. **PostgreSQL 16** (with health check)
2. **FastAPI app** (waits for DB, runs migrations, starts server)

The app will be available at `http://localhost:8000`.

### Stop

```bash
docker compose down

# Remove volumes too (deletes DB data)
docker compose down -v
```

---

## Design Decisions

### Why FastAPI?
FastAPI provides automatic OpenAPI documentation, native async support, and Pydantic integration for free. It's also one of the fastest Python web frameworks.

### Why PostgreSQL?
Relational data (job → recipients) is a natural fit for SQL. PostgreSQL has native UUID support, is production-proven, and is the industry standard for reliability.

### Why SQLAlchemy ORM?
It prevents SQL injection by design (ORM queries are parameterized automatically), provides a clean Pythonic interface, and integrates with Alembic for migrations.

### Why BackgroundTasks instead of Celery?
For this scale (hundreds to low thousands of certificates), FastAPI's built-in `BackgroundTasks` is sufficient and avoids the operational overhead of Redis + Celery workers. Adding Celery later is a natural scale-up path.

### Why ReportLab?
It's the most mature, pure-Python PDF generation library. No external binaries needed, works on all platforms.

### Why store file paths in PostgreSQL (not PDFs)?
Storing PDF binary data in the DB would bloat it rapidly. File paths are tiny strings. The files are served directly from disk, which is faster and doesn't load the DB.

### Why continue processing after individual failures?
In a batch of 100 recipients, a single failure shouldn't penalize the other 99 valid recipients. Each recipient is processed independently with its own try/except block.

---

## Interview Discussion Points

**Q: Why FastAPI?**
FastAPI auto-generates Swagger docs, has built-in Pydantic validation, supports async/await, and is one of the fastest Python frameworks. It lets you build APIs quickly without boilerplate.

**Q: Why PostgreSQL?**
It's reliable, supports UUIDs natively, has mature tooling, and is the industry standard. SQLAlchemy + Alembic integrate perfectly with it.

**Q: Why SQLAlchemy?**
It provides type-safe ORM queries, prevents SQL injection by default, and Alembic uses it for migrations. Writing raw SQL for every query would be harder to maintain.

**Q: Why BackgroundTasks instead of Celery?**
For this assignment's scale, it's much simpler — no Redis, no worker processes. BackgroundTasks runs after the response is sent. Celery would make sense at 100,000+ concurrent jobs.

**Q: How does bulk processing work?**
The API creates the job and all recipient records in one transaction, returns the `job_id`, then starts a background task. The background task iterates through all recipients, generates each certificate independently, and updates the DB.

**Q: How is progress calculated?**
I query the DB directly: `SELECT COUNT(*) WHERE status='COMPLETED'`. This is accurate even if the server restarts mid-job, because the state is in the DB — not in memory.

**Q: How are individual failures handled?**
Each recipient has its own `try/except` block. If `generate_certificate()` raises an exception, the error message is saved to `recipient.error_message`, the recipient is marked `FAILED`, and the loop continues to the next recipient.

**Q: Why store file paths instead of PDFs in PostgreSQL?**
Storing PDFs in the DB would make the DB huge and slow. File systems are optimized for serving binary files. We store the path, and FastAPI serves the file directly from disk using `FileResponse`.

**Q: How would you scale to 100,000 certificates?**
Replace `BackgroundTasks` with Celery + Redis. Each recipient would become a separate Celery task, allowing parallel processing across multiple workers. Add S3 for file storage so multiple workers can write to the same place.

**Q: How would you add Redis/Celery?**
1. Add `celery` and `redis` to requirements
2. Create `celery_app.py` with `Celery('tasks', broker='redis://localhost')`
3. Convert `process_bulk_job` into a `@celery.task`
4. Change `background_tasks.add_task(...)` to `process_bulk_job.delay(...)`

**Q: How would you add S3?**
Replace the local `generated_certificates/` directory with `boto3` S3 uploads. Instead of storing a local path in the DB, store the S3 key. Serve downloads via pre-signed S3 URLs instead of `FileResponse`.

**Q: How would you add authentication?**
Add `python-jose` + `passlib`. Create a `/auth/login` endpoint that returns a JWT. Use `HTTPBearer` security on all certificate endpoints. Add a `users` table.

**Q: How would you implement retries?**
Add a `PATCH /api/v1/certificates/jobs/{job_id}/retry` endpoint that re-queues all `FAILED` recipients. With Celery, use `autoretry_for=(Exception,)` with exponential backoff.

---

## Future Scope

The following features are intentionally not implemented (out of scope for this assignment) but are natural next steps:

- **Redis + Celery** for large-scale parallel certificate generation
- **S3 / Cloud object storage** for certificate PDFs
- **Email delivery** — automatically email certificates to recipients
- **Authentication** — JWT-based API auth for organizations
- **Multiple certificate templates** — allow custom designs per event
- **Retry failed certificates** — endpoint to re-process failed recipients
- **Job cancellation** — cancel a running job mid-processing
- **Rate limiting** — prevent abuse of the generation endpoint
- **Webhook notifications** — notify a URL when a job completes
