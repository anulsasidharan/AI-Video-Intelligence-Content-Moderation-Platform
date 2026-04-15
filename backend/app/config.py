from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    APP_NAME: str = "VidShield AI"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vidshield"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/vidshield"

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    @model_validator(mode="after")
    def _derive_urls(self) -> "Settings":
        """Derive Celery and sync DB URLs from injected base URLs.

        Injecting only DATABASE_URL and REDIS_URL (e.g. from GCP Secret Manager)
        is sufficient — sync and Celery URLs are derived automatically.
        """
        # Derive DATABASE_URL_SYNC from DATABASE_URL when still at default
        if "asyncpg" in self.DATABASE_URL and "localhost" in self.DATABASE_URL_SYNC:
            self.DATABASE_URL_SYNC = self.DATABASE_URL.replace(
                "postgresql+asyncpg", "postgresql+psycopg2"
            )
        # Derive Celery broker/backend from REDIS_URL
        base = self.REDIS_URL.rsplit("/", 1)[0]  # strip db number
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = f"{base}/1"
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = f"{base}/2"
        return self

    # ── Auth / JWT ───────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_RATE_LIMIT: int = 3  # max requests per 15-minute window
    FRONTEND_URL: str = "http://localhost:3000"

    # ── GCP ──────────────────────────────────────────────────
    GCP_PROJECT_ID: str = ""
    GCS_BUCKET_NAME: str = "vidshield-videos"
    GCS_PRESIGNED_URL_EXPIRE: int = 3600  # seconds
    # Optional: path to a service-account JSON key for signed URL generation.
    # Leave blank when running on GKE with Workload Identity (ADC is used instead).
    GCS_SERVICE_ACCOUNT_KEY_PATH: str = ""

    # ── RTMP ingest ───────────────────────────────────────────
    RTMP_INGEST_HOST: str = "ingest.vidshield.ai"

    # ── OpenAI ───────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MINI_MODEL: str = "gpt-4o-mini"

    # ── Pinecone ─────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "vidshield-embeddings"

    # ── SendGrid (Email notifications) ───────────────────────
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@orionvexa.ca"
    SENDGRID_FROM_NAME: str = "VidShield AI"

    # ── Twilio (WhatsApp notifications) ──────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"

    # -- Stripe ----------------------------------------------------
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_GROWTH_PRICE_ID: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:3000/dashboard/billing?success=true"
    STRIPE_CANCEL_URL: str = "http://localhost:3000/dashboard/billing?canceled=true"

    # ── Sentry ───────────────────────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ── Pagination ───────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
