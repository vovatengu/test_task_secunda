from __future__ import annotations

from uuid import UUID

from payments.domain.entities.payment import Payment
from payments.domain.interfaces.repositories import PaymentRepository


async def get_payment(repo: PaymentRepository, payment_id: UUID) -> Payment | None:
    return await repo.get_by_id(payment_id)
