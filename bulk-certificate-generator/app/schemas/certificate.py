from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID


# ---------- Request Schemas ----------

class RecipientRequest(BaseModel):
    name: str
    email: EmailStr

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Recipient name cannot be empty")
        return v.strip()


class CreateJobRequest(BaseModel):
    event_name: str
    certificate_title: str
    issue_date: date
    recipients: list[RecipientRequest]

    @field_validator("event_name")
    @classmethod
    def event_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("event_name cannot be empty")
        return v.strip()

    @field_validator("certificate_title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("certificate_title cannot be empty")
        return v.strip()

    @field_validator("recipients")
    @classmethod
    def recipients_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("recipients list cannot be empty")
        return v


# ---------- Response Schemas ----------

class JobCreatedResponse(BaseModel):
    job_id: UUID
    status: str
    total_count: int
    success_count: int
    failure_count: int


class JobStatusResponse(BaseModel):
    job_id: UUID
    status: str
    total_count: int
    success_count: int
    failure_count: int
    pending_count: int
    progress_percentage: float


class CertificateInfo(BaseModel):
    certificate_id: UUID
    recipient_name: str
    email: str
    status: str
    download_url: Optional[str] = None
    error: Optional[str] = None


class ListCertificatesResponse(BaseModel):
    job_id: UUID
    certificates: list[CertificateInfo]
