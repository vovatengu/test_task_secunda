from __future__ import annotations

import logging

from core.settings import Settings
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from payments.consumer.handlers import register_payment_consumer
from payments.infrastructure.messaging.rabbit_setup import declare_dead_letter_topology

logger = logging.getLogger(__name__)


def build_consumer_app(settings: Settings) -> FastStream:
    broker = RabbitBroker(settings.rabbitmq_url)

    async def on_startup() -> None:
        await declare_dead_letter_topology(settings.rabbitmq_url)

    register_payment_consumer(broker, settings)

    return FastStream(
        broker,
        on_startup=[on_startup],
        logger=logger,
    )
