from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from payments.domain.entities.payment import Currency, Payment, PaymentStatus
from payments.infrastructure.persistence.models import PaymentRow


def _row_to_domain(row: PaymentRow) -> Payment:
    return Payment(
        id=row.id,
        amount=row.amount,
        currency=Currency(row.currency),
        description=row.description,
        metadata=dict(row.metadata_ or {}),
        status=PaymentStatus(row.status),
        idempotency_key=row.idempotency_key,
        webhook_url=row.webhook_url,
        created_at=row.created_at,
        processed_at=row.processed_at,
    )


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        row = await self._session.get(PaymentRow, payment_id)
        return None if row is None else _row_to_domain(row)

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        stmt = select(PaymentRow).where(PaymentRow.idempotency_key == key).limit(1)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return None if row is None else _row_to_domain(row)

    async def add(self, payment: Payment) -> None:
        row = PaymentRow(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency.value,
            description=payment.description,
            metadata_=payment.metadata,
            status=payment.status.value,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
        self._session.add(row)

    async def try_insert_new_payment(self, payment: Payment) -> bool:
        await self.add(payment)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            return False
        return True

    async def update(self, payment: Payment) -> None:
        row = await self._session.get(PaymentRow, payment.id)
        if row is None:
            return
        row.amount = payment.amount
        row.currency = payment.currency.value
        row.description = payment.description
        row.metadata_ = payment.metadata
        row.status = payment.status.value
        row.webhook_url = payment.webhook_url
        row.processed_at = payment.processed_at
