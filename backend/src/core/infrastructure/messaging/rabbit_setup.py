from __future__ import annotations

import logging

import aio_pika
from aio_pika import ExchangeType

from core.constants import PAYMENTS_DLQ, PAYMENTS_DLQ_ROUTING_KEY, PAYMENTS_DLX

logger = logging.getLogger(__name__)


async def declare_dead_letter_topology(rabbitmq_url: str) -> None:
    """Create DLX + DLQ before the main queue (which references x-dead-letter-exchange)."""
    connection = await aio_pika.connect_robust(rabbitmq_url)
    try:
        channel = await connection.channel()
        dlx = await channel.declare_exchange(PAYMENTS_DLX, ExchangeType.DIRECT, durable=True)
        dlq = await channel.declare_queue(PAYMENTS_DLQ, durable=True)
        await dlq.bind(dlx, routing_key=PAYMENTS_DLQ_ROUTING_KEY)
        logger.info("Declared RabbitMQ DLX %s and DLQ %s", PAYMENTS_DLX, PAYMENTS_DLQ)
    finally:
        await connection.close()
