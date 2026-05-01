"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    groq_api_key: str = Field(
        default="",
        description="Groq API key for LLM access",
    )

    cors_origins: str = Field(
        description="Comma-separated list of allowed CORS origins",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    model_name: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model to use",
    )

    model_temperature: float = Field(
        default=0.7,
        description="LLM temperature for generation",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton settings instance
settings = Settings()
