from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from core.infrastructure.messaging.retry_ack import manual_ack_with_retry
from core.infrastructure.messaging.topology import payments_events_exchange, payments_new_queue
from core.settings import Settings
from faststream.middlewares import AckPolicy
from faststream.rabbit.annotations import RabbitBroker, RabbitMessage
from payments.application.use_cases.process_payment_message import process_payment_message

logger = logging.getLogger(__name__)


def register_payment_consumer(broker: RabbitBroker, settings: Settings) -> None:
    exchange = payments_events_exchange()
    queue = payments_new_queue()

    @broker.subscriber(
        queue,
        exchange=exchange,
        ack_policy=AckPolicy.MANUAL,
    )
    async def handle_payment_created(
        body: dict[str, Any],
        msg: RabbitMessage,
        br: RabbitBroker,
    ) -> None:
        raw_id = body.get("payment_id")
        if not raw_id:
            logger.error("Invalid message (missing payment_id): %s", body)
            await msg.ack()
            return
        try:
            payment_id = UUID(str(raw_id))
        except (ValueError, TypeError):
            logger.error("Invalid payment_id in message: %s", body)
            await msg.ack()
            return

        async def execute() -> None:
            await process_payment_message(payment_id, settings)

        await manual_ack_with_retry(
            msg,
            br,
            body,
            exchange,
            execute=execute,
            log_label=f"Payment {payment_id}",
        )
