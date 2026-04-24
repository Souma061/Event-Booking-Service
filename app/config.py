from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Event Booking Service"
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    CORS_ALLOW_ORIGIN_REGEX: str = ""

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/event_booking"
    )

    JWT_SECRET_KEY: str = Field(default="change_me_in_env")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ADMIN_SECRET_KEY: str | None = None

    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_BOOKING: str = "5/minute"
    RATE_LIMIT_RECOMMENDATION: str = "20/minute"

    CASHFREE_APP_ID: str = ""
    CASHFREE_SECRET_KEY: str = ""
    CASHFREE_ENVIRONMENT: str = "SANDBOX"
    CASHFREE_WEBHOOK_URL: str = ""
    CASHFREE_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS: int = 300

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SENDER_EMAIL: str = ""
    SMTP_SENDER_NAME: str = "Event Booking"

    FEATURE_WHATSAPP_ENABLED: bool = False
    FEATURE_LLM_RECOMMENDATIONS: bool = False


settings = Settings()
