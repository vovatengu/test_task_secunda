from __future__ import annotations

import asyncio
import json
import logging

import aio_pika
from aio_pika import DeliveryMode, ExchangeType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.constants import PAYMENTS_EXCHANGE, PAYMENTS_ROUTING_KEY
from core.settings import Settings
from payments.infrastructure.persistence.models import OutboxRow

logger = logging.getLogger(__name__)


async def run_outbox_relay(
    stop: asyncio.Event,
    settings: Settings,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    """Poll unpublished outbox rows and publish to RabbitMQ after the API transaction has committed.

    Each message is published and marked ``published`` in a single DB transaction with
    ``SELECT … FOR UPDATE SKIP LOCKED`` so multiple relay instances can run safely and a
    successful publish is always paired with the DB update (no partial batch duplicates).
    """
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel(publisher_confirms=True)
        exchange = await channel.declare_exchange(PAYMENTS_EXCHANGE, ExchangeType.TOPIC, durable=True)

        while not stop.is_set():
            processed_in_round = 0
            try:
                while not stop.is_set():
                    async with session_maker() as session:
                        async with session.begin():
                            stmt = (
                                select(OutboxRow)
                                .where(OutboxRow.published.is_(False))
                                .order_by(OutboxRow.id)
                                .limit(1)
                                .with_for_update(skip_locked=True)
                            )
                            result = await session.execute(stmt)
                            row = result.scalar_one_or_none()
                            if row is None:
                                break

                            body = json.dumps(row.payload).encode()
                            await exchange.publish(
                                aio_pika.Message(
                                    body,
                                    delivery_mode=DeliveryMode.PERSISTENT,
                                    content_type="application/json",
                                ),
                                routing_key=PAYMENTS_ROUTING_KEY,
                            )
                            row.published = True
                            processed_in_round += 1
                            logger.debug(
                                "Published outbox id=%s payment_id=%s",
                                row.id,
                                row.payment_id,
                            )
            except Exception:
                logger.exception("Outbox relay iteration failed")

            if processed_in_round == 0:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=settings.outbox_poll_interval_seconds)
                except TimeoutError:
                    pass
    finally:
        await connection.close()
