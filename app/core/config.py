from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BI Analytics AI"
    app_env: Literal["development", "test", "production"] = "development"
    secret_key: str = Field("development-only-change-me-please", min_length=24)
    access_token_expire_minutes: int = 480
    data_provider: Literal["demo", "csv", "mysql"] = "demo"
    csv_production_path: str = "data/imports/current_production.csv"
    csv_max_upload_mb: int = Field(50, ge=1, le=500)
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "bi_analytics"
    db_user: str = "bi_readonly"
    db_password: str = ""
    db_pool_size: int = Field(3, ge=1, le=10)
    db_max_overflow: int = Field(2, ge=0, le=10)
    db_query_timeout_ms: int = Field(5000, ge=500, le=30000)
    db_max_rows: int = Field(1000, ge=1, le=5000)
    db_max_concurrent_queries: int = Field(3, ge=1, le=10)
    dashboard_cache_ttl_seconds: int = Field(60, ge=5, le=3600)
    ai_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus

        return (
            f"mysql+pymysql://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
