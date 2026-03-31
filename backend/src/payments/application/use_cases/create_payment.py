from __future__ import annotations

from datetime import UTC, datetime

from payments.domain.dtos.create_payment import CreatePaymentInput, CreatePaymentResult
from payments.domain.entities.payment import Payment
from payments.domain.exceptions.idempotency import IdempotencyKeyConflictError
from payments.domain.interfaces.repositories import OutboxWriter, PaymentRepository


def _matches_idempotent_create(existing: Payment, data: CreatePaymentInput) -> bool:
    return (
        existing.amount == data.amount
        and existing.currency == data.currency
        and existing.description == data.description
        and existing.metadata == data.metadata
        and existing.webhook_url == data.webhook_url
    )


async def create_payment(
    repo: PaymentRepository,
    outbox: OutboxWriter,
    data: CreatePaymentInput,
) -> CreatePaymentResult:
    existing = await repo.get_by_idempotency_key(data.idempotency_key)
    if existing is not None:
        if not _matches_idempotent_create(existing, data):
            raise IdempotencyKeyConflictError
        created = existing.created_at or datetime.now(tz=UTC)
        return CreatePaymentResult(
            payment_id=existing.id,
            status=existing.status,
            created_at=created,
        )

    now = datetime.now(tz=UTC)
    payment = Payment(
        amount=data.amount,
        currency=data.currency,
        description=data.description,
        idempotency_key=data.idempotency_key,
        webhook_url=data.webhook_url,
        metadata=data.metadata,
        created_at=now,
    )
    if not await repo.try_insert_new_payment(payment):
        existing = await repo.get_by_idempotency_key(data.idempotency_key)
        if existing is None:
            msg = "idempotency unique violation but row not found"
            raise RuntimeError(msg)
        if not _matches_idempotent_create(existing, data):
            raise IdempotencyKeyConflictError
        created = existing.created_at or datetime.now(tz=UTC)
        return CreatePaymentResult(
            payment_id=existing.id,
            status=existing.status,
            created_at=created,
        )
    await outbox.enqueue_payment_created(
        payment,
        {"type": "payment.created", "payment_id": str(payment.id)},
    )
    return CreatePaymentResult(
        payment_id=payment.id,
        status=payment.status,
        created_at=now,
    )
