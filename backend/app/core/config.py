import os
import secrets
from typing import List, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DataForge"
    
    # Generate a random secret if not set (for dev/test), but in prod should be set via env var
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://192.168.20.7:3000",
        "*"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    # Database
    # Using SQLite by default as per requirements
    DATA_DIR: str = os.getenv("DATA_DIR", "/data")
    DB_PATH: Union[str, None] = None
    SQLALCHEMY_DATABASE_URI: Union[str, None] = None

    # File Uploads
    UPLOAD_DIR: Union[str, None] = None
    EXPORT_DIR: Union[str, None] = None

    # Admin Settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@dataforge.local")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @model_validator(mode='after')
    def compute_paths(self) -> 'Settings':
        if self.DB_PATH is None:
            self.DB_PATH = os.path.join(self.DATA_DIR, "dataforge.db")
        if self.SQLALCHEMY_DATABASE_URI is None:
            self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.DB_PATH}"
        if self.UPLOAD_DIR is None:
            self.UPLOAD_DIR = os.path.join(self.DATA_DIR, "uploads")
        if self.EXPORT_DIR is None:
            self.EXPORT_DIR = os.path.join(self.DATA_DIR, "exports")
        return self

settings = Settings()

print(f"DEBUG: DATA_DIR is {settings.DATA_DIR}")
print(f"DEBUG: UPLOAD_DIR is {settings.UPLOAD_DIR}")

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
