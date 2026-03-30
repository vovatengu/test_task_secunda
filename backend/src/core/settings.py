from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "payment-processing"
    log_level: str = "INFO"

    api_key: str = Field(default="dev-api-key", validation_alias="API_KEY")

    # Postgres components — DB_HOST задаётся как `db` в .env.dev/.env.test
    db_name: str = Field(default="payments", validation_alias="DB_NAME")
    db_user: str = Field(default="postgres", validation_alias="DB_USER")
    db_password: str = Field(default="postgres", validation_alias="DB_PASSWORD")
    db_host: str = Field(default="localhost", validation_alias="DB_HOST")
    db_port: int = Field(default=5432, validation_alias="DB_PORT")
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URI")

    # RabbitMQ components — RABBITMQ_HOST задаётся как `rabbitmq` в .env.dev/.env.test
    rabbitmq_user: str = Field(default="guest", validation_alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(default="guest", validation_alias="RABBITMQ_PASSWORD")
    rabbitmq_host: str = Field(default="localhost", validation_alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(default=5672, validation_alias="RABBITMQ_PORT")
    rabbitmq_url: str | None = Field(default=None, validation_alias="RABBITMQ_URL")

    gateway_delay_min_seconds: float = 2.0
    gateway_delay_max_seconds: float = 5.0
    gateway_success_probability: float = 0.9

    webhook_timeout_seconds: float = 30.0
    outbox_poll_interval_seconds: float = 1.0

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str | None, info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=info.data.get("db_user"),
                password=info.data.get("db_password"),
                host=info.data.get("db_host"),
                port=info.data.get("db_port"),
                path=info.data.get("db_name"),
            )
        )

    @field_validator("rabbitmq_url", mode="before")
    @classmethod
    def assemble_rabbitmq_url(cls, v: str | None, info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        user = info.data.get("rabbitmq_user", "guest")
        password = info.data.get("rabbitmq_password", "guest")
        host = info.data.get("rabbitmq_host", "localhost")
        port = info.data.get("rabbitmq_port", 5672)
        return f"amqp://{user}:{password}@{host}:{port}/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
