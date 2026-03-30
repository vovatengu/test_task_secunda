from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from core.settings import get_settings
from db.session import get_db
from payments.domain.repositories import OutboxWriter
from payments.infrastructure.outbox import NoOpOutboxWriter
from payments.infrastructure.persistence.payment_repository import SqlAlchemyPaymentRepository

_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(x_api_key: str | None = Security(_api_key_scheme)) -> None:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


_MAX_IDEMPOTENCY_KEY_LEN = 255


async def require_idempotency_key(
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            description="Unique key for safe request retries; required on create.",
        ),
    ],
) -> str:
    key = idempotency_key.strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Idempotency-Key must be a non-empty string",
        )
    if len(key) > _MAX_IDEMPOTENCY_KEY_LEN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Idempotency-Key must be at most {_MAX_IDEMPOTENCY_KEY_LEN} characters",
        )
    return key


async def get_payment_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SqlAlchemyPaymentRepository:
    return SqlAlchemyPaymentRepository(session)


async def get_outbox_writer() -> OutboxWriter:
    """Swap for a real outbox implementation when persistence + broker are wired."""
    return NoOpOutboxWriter()
