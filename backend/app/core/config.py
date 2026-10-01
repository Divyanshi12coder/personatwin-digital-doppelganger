"""Application settings, loaded from environment variables (and an optional .env file).

Every secret (JWT secret, AI keys, database password) comes from the environment.
Nothing secret is ever sent to the frontend.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The pgvector column dimension is fixed by the migration. Both embedding
# providers are configured to emit vectors of exactly this size.
EMBEDDING_DIM = 384


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---------------------------------------------------------------
    APP_NAME: str = "PersonaTwin"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    API_PREFIX: str = "/api"
    LOG_LEVEL: str = "INFO"

    # --- Database ----------------------------------------------------------
    # PostgreSQL + pgvector in Docker/production. SQLite is supported for
    # quick local runs and the test-suite (vector search falls back to Python).
    DATABASE_URL: str = "sqlite:///./personatwin.db"

    # --- Auth --------------------------------------------------------------
    JWT_SECRET: str = "dev-only-change-me-dev-only-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    # --- CORS --------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080"

    # --- AI provider (LLM) -------------------------------------------------
    # "anthropic" | "openai" | "demo". "demo" needs no key and composes grounded
    # answers directly from retrieved memories (clearly labelled in the UI).
    AI_PROVIDER: Literal["anthropic", "openai", "demo"] = "demo"
    AI_API_KEY: str = ""
    AI_MODEL: str = ""
    AI_BASE_URL: str = ""  # optional override (e.g. an OpenAI-compatible gateway)
    AI_MAX_TOKENS: int = 2000
    AI_EFFORT: Literal["low", "medium", "high"] = "medium"  # Anthropic adaptive-thinking effort
    AI_ENABLE_FALLBACKS: bool = True  # Anthropic server-side refusal fallbacks
    AI_TIMEOUT_SECONDS: float = 90.0

    # --- Embeddings --------------------------------------------------------
    # "local" = deterministic hashed n-gram embeddings (no network, no key).
    # "openai" = OpenAI embeddings API, reduced to EMBEDDING_DIM dimensions.
    EMBEDDING_PROVIDER: Literal["local", "openai"] = "local"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_BASE_URL: str = ""

    # --- Retrieval / memory ------------------------------------------------
    CHUNK_SIZE_CHARS: int = 900
    CHUNK_OVERLAP_CHARS: int = 150
    SHORT_TERM_MEMORY_MESSAGES: int = 10

    # --- Uploads / URL import ---------------------------------------------
    MAX_UPLOAD_BYTES: int = 2 * 1024 * 1024
    MAX_KNOWLEDGE_CHARS: int = 200_000
    URL_FETCH_TIMEOUT_SECONDS: float = 10.0

    # --- Rate limits (in-process): auth per client IP, chat per user ------
    AUTH_RATE_LIMIT_PER_MINUTE: int = 20
    CHAT_RATE_LIMIT_PER_MINUTE: int = 30

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        # Render/Heroku style URLs -> SQLAlchemy psycopg3 driver.
        if v.startswith("postgres://"):
            v = "postgresql+psycopg://" + v[len("postgres://") :]
        elif v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    @model_validator(mode="after")
    def check_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET.startswith("dev-only") or len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be set to a strong value (>= 32 chars) in production")
        # A missing AI_API_KEY is deliberately not fatal: the AI service downgrades
        # to demo mode and reports that through /api/health and every chat reply.
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def resolved_ai_model(self) -> str:
        if self.AI_MODEL:
            return self.AI_MODEL
        return {"anthropic": "claude-opus-5", "openai": "gpt-4o-mini"}.get(self.AI_PROVIDER, "demo-composer")


@lru_cache
def get_settings() -> Settings:
    return Settings()
