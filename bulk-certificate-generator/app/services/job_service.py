import uuid
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.models.generation_job import GenerationJob
from app.models.recipient import Recipient
from app.schemas.certificate import CreateJobRequest
from app.services.certificate_service import generate_certificate
from app.database.database import SessionLocal  # module-level so tests can patch it


def create_job(db: Session, request: CreateJobRequest) -> GenerationJob:
    """
    Create a new GenerationJob and associated Recipient records.
    Returns the created job.
    """
    job = GenerationJob(
        id=uuid.uuid4(),
        status="PENDING",
        total_count=len(request.recipients),
        success_count=0,
        failure_count=0,
        event_name=request.event_name,
        certificate_title=request.certificate_title,
        issue_date=request.issue_date,
        created_at=datetime.now(UTC),
    )
    db.add(job)
    db.flush()  # Get the job.id without committing

    for r in request.recipients:
        recipient = Recipient(
            id=uuid.uuid4(),
            job_id=job.id,
            name=r.name,
            email=r.email,
            certificate_status="PENDING",
            created_at=datetime.now(UTC),
        )
        db.add(recipient)

    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> GenerationJob | None:
    """Retrieve a job by its UUID string."""
    try:
        uid = uuid.UUID(job_id)
    except ValueError:
        return None
    return db.query(GenerationJob).filter(GenerationJob.id == uid).first()


def get_recipient(db: Session, certificate_id: str) -> Recipient | None:
    """Retrieve a recipient by its UUID string."""
    try:
        uid = uuid.UUID(certificate_id)
    except ValueError:
        return None
    return db.query(Recipient).filter(Recipient.id == uid).first()


def get_job_recipients(db: Session, job_id: str) -> list[Recipient]:
    """Get all recipients for a given job."""
    try:
        uid = uuid.UUID(job_id)
    except ValueError:
        return []
    return db.query(Recipient).filter(Recipient.job_id == uid).all()


def process_bulk_job(job_id: str) -> None:
    """
    Background task: process all recipients for a job.
    
    Creates its own DB session so it can run safely in a background thread.
    Each recipient is processed independently — a failure on one does NOT
    stop the others.
    """
    db: Session = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == uuid.UUID(job_id)).first()
        if not job:
            return

        # Mark job as PROCESSING
        job.status = "PROCESSING"
        job.started_at = datetime.now(UTC)
        db.commit()

        recipients = db.query(Recipient).filter(Recipient.job_id == job.id).all()

        for recipient in recipients:
            # Mark recipient as PROCESSING
            recipient.certificate_status = "PROCESSING"
            db.commit()

            try:
                cert_path = generate_certificate(
                    recipient_name=recipient.name,
                    event_name=job.event_name,
                    certificate_title=job.certificate_title,
                    issue_date=job.issue_date,
                    certificate_id=str(recipient.id),
                )
                recipient.certificate_status = "COMPLETED"
                recipient.certificate_path = cert_path
                recipient.completed_at = datetime.now(UTC)
            except Exception as e:
                recipient.certificate_status = "FAILED"
                recipient.error_message = str(e)
                recipient.completed_at = datetime.now(UTC)

            db.commit()

        # Recalculate counts from actual recipient records
        success_count = db.query(Recipient).filter(
            Recipient.job_id == job.id,
            Recipient.certificate_status == "COMPLETED"
        ).count()
        failure_count = db.query(Recipient).filter(
            Recipient.job_id == job.id,
            Recipient.certificate_status == "FAILED"
        ).count()

        job.success_count = success_count
        job.failure_count = failure_count
        job.completed_at = datetime.now(UTC)

        if failure_count == 0:
            job.status = "COMPLETED"
        elif success_count == 0:
            job.status = "FAILED"
        else:
            job.status = "COMPLETED_WITH_ERRORS"

        db.commit()

    except Exception as e:
        # Something catastrophic happened — mark job as FAILED
        try:
            db.rollback()
            job = db.query(GenerationJob).filter(GenerationJob.id == uuid.UUID(job_id)).first()
            if job:
                job.status = "FAILED"
                job.completed_at = datetime.now(UTC)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
