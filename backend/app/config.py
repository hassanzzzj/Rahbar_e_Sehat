"""
Application configuration using pydantic-settings for environment-driven configuration.
All sensitive values are loaded from environment variables, never hardcoded.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="rahbar-e-sehat")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    secret_key: str = Field(min_length=32)

    # API Server
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_prefix: str = Field(default="/api/v1")

    # Database
    database_url: str = Field()
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=100)

    # Groq (free-tier, OpenAI-compatible LLM + Whisper API)
    groq_api_key: str = Field(default="")
    groq_api_base: str = Field(default="https://api.groq.com/openai/v1")
    groq_model_name: str = Field(default="llama-3.3-70b-versatile")
    groq_whisper_model_name: str = Field(default="whisper-large-v3")

    # Vector Store
    vector_store_path: str = Field(default="/app/data/vector_store")
    vector_store_type: str = Field(default="faiss")

    # Facility Matching
    facility_search_default_radius_km: float = Field(default=50.0, ge=1.0, le=500.0)
    facility_max_results: int = Field(default=5, ge=1, le=20)
    facility_data_path: str = Field(default="/app/data/facilities.json")

    # Medicine Availability
    medicine_data_path: str = Field(default="/app/data/medicines.json")
    medicine_cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, ge=1)
    rate_limit_burst: int = Field(default=10, ge=1)

    # Security
    encryption_key: str = Field(min_length=32)
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168)

    # Data Retention
    session_data_retention_days: int = Field(default=30, ge=1, le=365)

    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]
