from __future__ import annotations

from core.constants import (
    PAYMENTS_DLQ,
    PAYMENTS_DLQ_ROUTING_KEY,
    PAYMENTS_DLX,
    PAYMENTS_EXCHANGE,
    PAYMENTS_QUEUE_NAME,
    PAYMENTS_ROUTING_KEY,
)
from faststream.rabbit.schemas import RabbitExchange, RabbitQueue
from faststream.rabbit.schemas.constants import ExchangeType


def payments_events_exchange() -> RabbitExchange:
    return RabbitExchange(
        name=PAYMENTS_EXCHANGE,
        type=ExchangeType.TOPIC,
        durable=True,
    )


def payments_new_queue() -> RabbitQueue:
    return RabbitQueue(
        name=PAYMENTS_QUEUE_NAME,
        durable=True,
        routing_key=PAYMENTS_ROUTING_KEY,
        arguments={
            "x-dead-letter-exchange": PAYMENTS_DLX,
            "x-dead-letter-routing-key": PAYMENTS_DLQ_ROUTING_KEY,
        },
    )
