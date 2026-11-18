from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "AFTR API"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "insecure-default-change-me-in-production-random-secret-key-32b"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://aftr_user:aftr_password@localhost:5432/aftr_db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Supabase Auth
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_JWT_SECRET: str = "placeholder-jwt-secret-min-32-bytes-secure-aftr"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder-service-role-key"
    
    # Business Rules
    INVITATION_EXPIRATION_HOURS: int = 72
    INITIAL_INVITE_QUOTA: int = 3
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://aftr.app",
    ]


settings = Settings()
