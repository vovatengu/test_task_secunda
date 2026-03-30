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
    """Poll unpublished outbox rows and publish to payments.events (routing key payments.new)."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(PAYMENTS_EXCHANGE, ExchangeType.TOPIC, durable=True)
        while not stop.is_set():
            try:
                async with session_maker() as session:
                    stmt = (
                        select(OutboxRow)
                        .where(OutboxRow.published.is_(False))
                        .order_by(OutboxRow.id)
                        .limit(50)
                    )
                    result = await session.execute(stmt)
                    rows = result.scalars().all()
                    for row in rows:
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
                    if rows:
                        await session.commit()
                        logger.debug("Published %s outbox message(s)", len(rows))
            except Exception:
                logger.exception("Outbox relay iteration failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=settings.outbox_poll_interval_seconds)
            except TimeoutError:
                pass
    finally:
        await connection.close()
