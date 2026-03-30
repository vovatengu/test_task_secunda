from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.settings import get_settings
from db.session import get_db
from payments.domain.repositories import OutboxWriter
from payments.infrastructure.outbox import NoOpOutboxWriter
from payments.infrastructure.persistence.payment_repository import SqlAlchemyPaymentRepository


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


async def get_payment_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SqlAlchemyPaymentRepository:
    return SqlAlchemyPaymentRepository(session)


async def get_outbox_writer() -> OutboxWriter:
    """Swap for a real outbox implementation when persistence + broker are wired."""
    return NoOpOutboxWriter()
