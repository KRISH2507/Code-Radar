import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    """
    Centralized configuration management for Code Radar backend.
    All settings must come from environment variables.
    """
    
    # Database
    DATABASE_URL: str
    
    # JWT & Security
    JWT_SECRET: str
    
    # Redis Configuration (optional for local dev)
    REDIS_URL: Optional[str] = None
    
    # Email Service
    EMAILJS_SERVICE_ID: Optional[str] = None
    EMAILJS_TEMPLATE_ID: Optional[str] = None
    EMAILJS_PUBLIC_KEY: Optional[str] = None
    EMAILJS_PRIVATE_KEY: Optional[str] = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    def __init__(self):
        """Load and validate required environment variables."""
        # Required settings
        self.DATABASE_URL = self._get_required_env("DATABASE_URL")
        self.JWT_SECRET = self._get_required_env("JWT_SECRET")
        
        # Optional settings — won't crash if missing
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID")
        self.EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID")
        self.EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY")
        self.EMAILJS_PRIVATE_KEY = os.getenv("EMAILJS_PRIVATE_KEY")
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
        
        # Validate Redis URL format only if provided
        if self.REDIS_URL:
            self._validate_redis_url()
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise clear error."""
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Missing required environment variable: {key}\n"
                f"Please set {key} in your .env file or environment."
            )
        return value
    
    def _validate_redis_url(self) -> None:
        """Validate Redis URL format for Redis Cloud compatibility."""
        if not self.REDIS_URL.startswith(("redis://", "rediss://")):
            print(
                f"WARNING: Invalid REDIS_URL format: {self.REDIS_URL}\n"
                f"Expected format: redis://<PASSWORD>@<HOST>:<PORT>/0\n"
                f"Redis features will be disabled."
            )
            self.REDIS_URL = None

# Global settings instance
settings = Settings()
