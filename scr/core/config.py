from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Piano Site"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://autocloud:autocloud123@localhost:5432/autocloud",
        description="Production: postgresql+asyncpg://user:pass@host:5432/db"
    )

    USE_SQLITE_FOR_DEV: bool = Field(default=True, description="Use SQLite in dev mode")
    
    JWT_SECRET_KEY: str = Field(default="change-this-in-production-32bytes!", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    RATE_LIMIT_REGISTER: str = "5/hour"
    RATE_LIMIT_LOGIN: str = "10/minute"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "REDACTED"
    SMTP_PASSWORD: str = "REDACTED"
    SMTP_FROM_EMAIL: str = "Piano jjk site <soldathekler@gmail.com>"
    SMTP_USE_TLS: bool = True

    FRONTEND_URL: str = "http://localhost:8000"
    
    CORS_ORIGINS: list[str] = ["*"]
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    model_config = SettingsConfigDict(
        env_file=".env",           
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()

"""
# .env
JWT_SECRET_KEY=your-super-secret-key-at-least-32-bytes-long!!!
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
RATE_LIMIT_LOGIN=20/minute
DEBUG=True
"""