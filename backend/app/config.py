"""Application settings loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Auth
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 12

    # Database
    mysql_url: str = "mysql+pymysql://medishield:dev@localhost:3306/medishield"

    # Vector store
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "policy_chunks"

    # Observability
    langsmith_api_key: str = ""
    langsmith_tracing: bool = False
    langsmith_project: str = "medishield-dev"
    log_level: str = "INFO"

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # Storage
    upload_dir: str = "./uploads"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
