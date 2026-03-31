from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from core.constants import API_V1_PREFIX
from payments.application.use_cases.create_payment import create_payment
from payments.application.use_cases.get_payment import get_payment
from payments.domain.dtos.create_payment import CreatePaymentInput
from payments.domain.exceptions.idempotency import IdempotencyKeyConflictError
from payments.domain.interfaces.repositories import OutboxWriter
from payments.infrastructure.persistence.payment_repository import SqlAlchemyPaymentRepository
from payments.presentation.api.schemas import (
    CreatePaymentRequest,
    PaymentCreatedResponse,
    PaymentDetailResponse,
)
from payments.presentation.dependencies import (
    get_outbox_writer,
    get_payment_repository,
    require_api_key,
    require_idempotency_key,
)

router = APIRouter(prefix=f"{API_V1_PREFIX}/payments", tags=["payments"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PaymentCreatedResponse,
)
async def create_payment_endpoint(
    _: Annotated[None, Depends(require_api_key)],
    body: CreatePaymentRequest,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    repo: Annotated[SqlAlchemyPaymentRepository, Depends(get_payment_repository)],
    outbox: Annotated[OutboxWriter, Depends(get_outbox_writer)],
) -> PaymentCreatedResponse:
    try:
        result = await create_payment(
            repo,
            outbox,
            CreatePaymentInput(
                amount=body.amount,
                currency=body.currency,
                description=body.description,
                metadata=body.metadata,
                webhook_url=str(body.webhook_url) if body.webhook_url is not None else None,
                idempotency_key=idempotency_key,
            ),
        )
    except IdempotencyKeyConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used with different parameters",
        ) from None
    return PaymentCreatedResponse(
        payment_id=result.payment_id,
        status=result.status,
        created_at=result.created_at,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailResponse,
)
async def get_payment_endpoint(
    _: Annotated[None, Depends(require_api_key)],
    payment_id: UUID,
    repo: Annotated[SqlAlchemyPaymentRepository, Depends(get_payment_repository)],
) -> PaymentDetailResponse:
    payment = await get_payment(repo, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return PaymentDetailResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )
