from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from payments.domain.entities.payment import Currency, PaymentStatus


@dataclass(frozen=True, slots=True)
class CreatePaymentInput:
    amount: Decimal
    currency: Currency
    description: str | None
    webhook_url: str | None
    idempotency_key: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CreatePaymentResult:
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime
