from pathlib import Path
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str
    JWT_SECRET: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    JWT_ISSUER: str = "code-radar"
    JWT_AUDIENCE: str = "code-radar-api"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: Optional[str] = None
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ENABLE_CORS_TEST_ENDPOINT: bool = True
    REFRESH_COOKIE_NAME: str = "code_radar_refresh_token"
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_SAMESITE: str = "lax"
    USE_SECURE_COOKIES: bool = False

    EMAILJS_SERVICE_ID: Optional[str] = None
    EMAILJS_TEMPLATE_ID: Optional[str] = None
    EMAILJS_PUBLIC_KEY: Optional[str] = None
    EMAILJS_PRIVATE_KEY: Optional[str] = None

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None

    HEALTHCHECK_INCLUDE_REDIS: bool = True
    RATE_LIMIT_SCAN_PER_HOUR: int = 10
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 5
    RATE_LIMIT_GENERAL_PER_MINUTE: int = 100
    RATE_LIMIT_UNAUTH_PER_MINUTE: int = 20

    @model_validator(mode="after")
    def ensure_jwt_secret(self) -> "Settings":
        resolved = (self.JWT_SECRET or self.SECRET_KEY or "").strip()
        if len(resolved) < 16:
            raise ValueError("JWT secret must be at least 16 characters long (JWT_SECRET or SECRET_KEY)")
        self.JWT_SECRET = resolved
        return self

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        value_lc = value.lower().strip()
        if value_lc not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
        return value_lc

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must start with redis:// or rediss://")
        return value

    @property
    def allowed_origins(self) -> List[str]:
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins


settings = Settings()
