from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from core.constants import MAX_PAYMENT_PROCESS_ATTEMPTS, PAYMENTS_ROUTING_KEY, RETRY_COUNT_HEADER
from faststream.rabbit.annotations import RabbitBroker, RabbitMessage
from faststream.rabbit.schemas import RabbitExchange

logger = logging.getLogger(__name__)


def _retry_count(headers: dict[str, Any]) -> int:
    raw = headers.get(RETRY_COUNT_HEADER, 0)
    if raw is None:
        return 0
    if isinstance(raw, bytes):
        raw = raw.decode()
    return int(raw)


async def manual_ack_with_retry(
    msg: RabbitMessage,
    br: RabbitBroker,
    body: dict[str, Any],
    exchange: RabbitExchange,
    *,
    execute: Callable[[], Awaitable[None]],
    log_label: str = "Message",
) -> None:
    """On success: ack. On failure: republish with incremented retry header or reject to DLQ."""
    try:
        await execute()
        await msg.ack()
    except Exception:
        retry = _retry_count(msg.headers)
        logger.exception(
            "%s processing failed (retry=%s/%s)",
            log_label,
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
