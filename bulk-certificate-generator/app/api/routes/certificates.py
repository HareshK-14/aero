from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.certificate import (
    CreateJobRequest,
    JobCreatedResponse,
    JobStatusResponse,
    ListCertificatesResponse,
    CertificateInfo,
)
from app.services import job_service
from app.models.recipient import Recipient
from app.utils.file_utils import is_safe_path

router = APIRouter(prefix="/api/v1/certificates", tags=["Certificates"])


@router.post(
    "/jobs",
    response_model=JobCreatedResponse,
    status_code=201,
    summary="Create a bulk certificate generation job",
    description="Submit a list of recipients to generate certificates in bulk. Returns a job ID to track progress.",
)
def create_generation_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = job_service.create_job(db, request)
    background_tasks.add_task(job_service.process_bulk_job, str(job.id))
    return JobCreatedResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status and progress",
    description="Returns the current status and processing progress of a generation job.",
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    # Calculate counts from actual recipient records for accuracy
    from app.models.recipient import Recipient
    import uuid
    uid = uuid.UUID(job_id)

    success_count = db.query(Recipient).filter(
        Recipient.job_id == uid,
        Recipient.certificate_status == "COMPLETED"
    ).count()
    failure_count = db.query(Recipient).filter(
        Recipient.job_id == uid,
        Recipient.certificate_status == "FAILED"
    ).count()
    pending_count = db.query(Recipient).filter(
        Recipient.job_id == uid,
        Recipient.certificate_status.in_(["PENDING", "PROCESSING"])
    ).count()

    processed = success_count + failure_count
    progress = round((processed / job.total_count * 100), 1) if job.total_count > 0 else 0.0

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
        success_count=success_count,
        failure_count=failure_count,
        pending_count=pending_count,
        progress_percentage=progress,
    )


@router.get(
    "/jobs/{job_id}/certificates",
    response_model=ListCertificatesResponse,
    summary="List all certificates for a job",
    description="Returns all recipient certificate records including status and download URLs.",
)
def list_certificates(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")

    recipients = job_service.get_job_recipients(db, job_id)

    certificates = []
    for r in recipients:
        download_url = None
        if r.certificate_status == "COMPLETED":
            download_url = f"/api/v1/certificates/{r.id}/download"

        certificates.append(
            CertificateInfo(
                certificate_id=r.id,
                recipient_name=r.name,
                email=r.email,
                status=r.certificate_status,
                download_url=download_url,
                error=r.error_message,
            )
        )

    return ListCertificatesResponse(job_id=job.id, certificates=certificates)


@router.get(
    "/{certificate_id}/download",
    summary="Download a generated certificate PDF",
    description="Returns the PDF file for a completed certificate. Returns 404 if not found.",
)
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    recipient = job_service.get_recipient(db, certificate_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if recipient.certificate_status != "COMPLETED" or not recipient.certificate_path:
        raise HTTPException(status_code=404, detail="Certificate has not been generated yet")

    file_path = Path(recipient.certificate_path)

    # Security: verify path is within storage directory
    if not is_safe_path(file_path):
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Certificate file not found on disk")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"certificate_{certificate_id}.pdf",
    )
