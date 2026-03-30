from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "payment-processing"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/payments"
    api_key: str = "dev-api-key"

    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    gateway_delay_min_seconds: float = 2.0
    gateway_delay_max_seconds: float = 5.0
    gateway_success_probability: float = 0.9

    webhook_timeout_seconds: float = 30.0
    outbox_poll_interval_seconds: float = 1.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
