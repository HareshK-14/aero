import os
import re
from pathlib import Path
from app.config import settings


def safe_filename(name: str) -> str:
    """
    Convert a string to a safe filename by removing special characters.
    Prevents path traversal and other filesystem issues.
    """
    # Remove everything that is not alphanumeric, hyphen, or underscore
    safe = re.sub(r"[^\w\-]", "_", name)
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_")


def get_certificate_path(certificate_id: str) -> Path:
    """Return the absolute path for a certificate PDF file."""
    storage = Path(settings.certificate_storage_path).resolve()
    filename = f"certificate_{certificate_id}.pdf"
    return storage / filename


def is_safe_path(path: Path) -> bool:
    """
    Verify the resolved path is within the certificate storage directory.
    Prevents path traversal attacks.
    """
    storage = Path(settings.certificate_storage_path).resolve()
    try:
        path.resolve().relative_to(storage)
        return True
    except ValueError:
        return False
