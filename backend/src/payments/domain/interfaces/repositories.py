from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from payments.domain.entities.payment import Payment


class PaymentRepository(Protocol):
    async def get_by_id(self, payment_id: UUID) -> Payment | None: ...

    async def get_by_idempotency_key(self, key: str) -> Payment | None: ...

    async def add(self, payment: Payment) -> None: ...

    async def try_insert_new_payment(self, payment: Payment) -> bool: ...

    async def update(self, payment: Payment) -> None: ...


class OutboxWriter(Protocol):
    async def enqueue_payment_created(self, payment: Payment, payload: dict[str, Any]) -> None: ...
