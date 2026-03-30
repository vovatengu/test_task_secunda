from __future__ import annotations

import logging
from collections.abc import Callable

from core.infrastructure.messaging.rabbit_setup import declare_dead_letter_topology
from core.settings import Settings
from faststream import FastStream
from faststream.rabbit import RabbitBroker

logger = logging.getLogger(__name__)


def build_rabbit_consumer_app(
    settings: Settings,
    register_subscribers: Callable[[RabbitBroker, Settings], None],
) -> FastStream:
    """Wire FastStream + RabbitMQ broker and run DLX/DLQ setup on startup."""
    broker = RabbitBroker(settings.rabbitmq_url)

    async def on_startup() -> None:
        await declare_dead_letter_topology(settings.rabbitmq_url)

    register_subscribers(broker, settings)

    return FastStream(
        broker,
        on_startup=[on_startup],
        logger=logger,
    )
