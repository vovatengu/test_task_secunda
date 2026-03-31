from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from payments.domain.entities.payment import Payment
from payments.domain.interfaces.repositories import OutboxWriter
from payments.infrastructure.persistence.models import OutboxRow


class SqlAlchemyOutboxWriter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue_payment_created(self, payment: Payment, payload: dict[str, Any]) -> None:
        row = OutboxRow(
            id=uuid4(),
            payment_id=payment.id,
            payload=payload,
            published=False,
        )
        self._session.add(row)
