from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from core.settings import Settings
from db.session import get_session_maker
from payments.domain.entities import PaymentStatus
from payments.infrastructure.gateway_emulator import emulate_payment_gateway
from payments.infrastructure.persistence.payment_repository import SqlAlchemyPaymentRepository
from payments.infrastructure.webhook_client import post_webhook_with_retry

logger = logging.getLogger(__name__)


def _webhook_payload(
    payment_id: UUID,
    status: PaymentStatus,
    amount: Decimal,
    currency: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "payment_id": str(payment_id),
        "status": status.value,
        "amount": str(amount),
        "currency": currency,
        "metadata": metadata,
    }


async def process_payment_message(payment_id: UUID, settings: Settings) -> None:
    """Process a single payment.created event: gateway → DB → optional webhook."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        repo = SqlAlchemyPaymentRepository(session)
        payment = await repo.get_by_id(payment_id)
        if payment is None:
            msg = f"payment not found: {payment_id}"
            raise ValueError(msg)
        if payment.status != PaymentStatus.PENDING:
            logger.info("Skipping already processed payment %s (%s)", payment_id, payment.status)
            return

        gateway_ok = await emulate_payment_gateway(settings)
        now = datetime.now(tz=UTC)
        if not gateway_ok:
            payment.status = PaymentStatus.FAILED
            payment.processed_at = now
            await repo.update(payment)
            await session.commit()
            logger.info("Payment %s marked failed after gateway emulation", payment_id)
            return

        payment.status = PaymentStatus.SUCCEEDED
        payment.processed_at = now
        webhook_url = payment.webhook_url
        payload = _webhook_payload(
            payment.id,
            payment.status,
            payment.amount,
            payment.currency.value,
            payment.metadata,
        )
        await repo.update(payment)
        await session.commit()

    if webhook_url:
        ok = await post_webhook_with_retry(webhook_url, payload, settings)
        if not ok:
            logger.error(
                "Webhook delivery failed after retries for payment %s (status still succeeded)",
                payment_id,
            )
