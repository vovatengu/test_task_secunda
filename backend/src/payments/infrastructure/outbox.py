from __future__ import annotations

from typing import Any

from payments.domain.entities import Payment
from payments.domain.repositories import OutboxWriter


class NoOpOutboxWriter:
    """Placeholder until outbox persistence + publisher are wired."""

    async def enqueue_payment_created(self, payment: Payment, payload: dict[str, Any]) -> None:
        _ = (payment, payload)
