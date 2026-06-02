from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fact-Check Agent"
    environment: str = "development"
    database_url: str = "sqlite:///./storage/factcheck.db"

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1", validation_alias="OPENAI_MODEL")
    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")
    serper_api_key: str | None = Field(default=None, validation_alias="SERPER_API_KEY")

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
    ]
    storage_dir: Path = Path("storage")
    max_upload_mb: int = 20
    search_results_per_claim: int = 6
    request_timeout_seconds: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    (settings.storage_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (settings.storage_dir / "reports").mkdir(parents=True, exist_ok=True)
    return settings

