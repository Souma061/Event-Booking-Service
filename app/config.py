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

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SENDER_EMAIL: str = ""
    SMTP_SENDER_NAME: str = "Event Booking"

    FEATURE_WHATSAPP_ENABLED: bool = False
    FEATURE_LLM_RECOMMENDATIONS: bool = False


settings = Settings()
