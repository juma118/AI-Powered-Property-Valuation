import json
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/proptech"

    # Auth / JWT
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # External APIs
    rentcast_api_key: str = ""
    google_maps_api_key: str = ""
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # Infra
    redis_url: str = "redis://redis:6379/0"

    # Behavior
    use_mock_data: bool = True

    # CORS — stored as a raw string (comma-separated or JSON list) so that
    # pydantic-settings does not attempt to JSON-decode it from the env var.
    # Consume the parsed value via `cors_origins_list`.
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse `cors_origins` into a list (accepts comma-separated or JSON)."""
        value = (self.cors_origins or "").strip()
        if not value:
            return ["http://localhost:3000"]
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except Exception:
                pass
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def embedding_dim(self) -> int:
        return 1536

    # Uppercase aliases consumed by the service layer (rentcast/enrichment/ai).
    @property
    def USE_MOCK_DATA(self) -> bool:
        return self.use_mock_data

    @property
    def RENTCAST_API_KEY(self) -> str:
        return self.rentcast_api_key

    @property
    def GOOGLE_MAPS_API_KEY(self) -> str:
        return self.google_maps_api_key

    @property
    def OPENAI_API_KEY(self) -> str:
        return self.openai_api_key

    @property
    def OPENAI_EMBEDDING_MODEL(self) -> str:
        return self.openai_embedding_model

    @property
    def OPENAI_CHAT_MODEL(self) -> str:
        return self.openai_chat_model


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
