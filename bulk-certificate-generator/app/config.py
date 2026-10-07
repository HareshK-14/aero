from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db"
    certificate_storage_path: str = "./generated_certificates"
    organization_name: str = "Infosys"
    app_title: str = "Bulk Certificate Generator"
    app_version: str = "1.0.0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure the storage directory exists
Path(settings.certificate_storage_path).mkdir(parents=True, exist_ok=True)
