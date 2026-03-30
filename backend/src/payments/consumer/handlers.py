from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from core.constants import MAX_PAYMENT_PROCESS_ATTEMPTS, PAYMENTS_ROUTING_KEY, RETRY_COUNT_HEADER
from core.settings import Settings
from faststream.middlewares import AckPolicy
from faststream.rabbit.annotations import RabbitBroker, RabbitMessage
from payments.consumer.process_payment import process_payment_message
from payments.infrastructure.messaging.topology import payments_events_exchange, payments_new_queue

logger = logging.getLogger(__name__)


def _retry_count(headers: dict[str, Any]) -> int:
    raw = headers.get(RETRY_COUNT_HEADER, 0)
    if raw is None:
        return 0
    if isinstance(raw, bytes):
        raw = raw.decode()
    return int(raw)


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

        try:
            await process_payment_message(payment_id, settings)
            await msg.ack()
        except Exception:
            retry = _retry_count(msg.headers)
            logger.exception(
                "Processing failed for payment %s (retry=%s/%s)",
                payment_id,
                retry + 1,
                MAX_PAYMENT_PROCESS_ATTEMPTS,
            )
            if retry >= MAX_PAYMENT_PROCESS_ATTEMPTS - 1:
                await msg.reject(requeue=False)
                logger.error("Message sent to DLQ after %s attempts", MAX_PAYMENT_PROCESS_ATTEMPTS)
                return
            await br.publish(
                message=body,
                exchange=exchange,
                routing_key=PAYMENTS_ROUTING_KEY,
                headers={RETRY_COUNT_HEADER: retry + 1},
            )
            await msg.ack()
