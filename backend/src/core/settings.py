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


@lru_cache
def get_settings() -> Settings:
    return Settings()
