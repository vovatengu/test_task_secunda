from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from core.constants import WEBHOOK_BACKOFF_BASE_SECONDS, WEBHOOK_MAX_ATTEMPTS
from core.settings import Settings

logger = logging.getLogger(__name__)


async def post_webhook_with_retry(
    url: str,
    payload: dict[str, Any],
    settings: Settings,
) -> bool:
    """POST JSON to webhook URL with up to WEBHOOK_MAX_ATTEMPTS and exponential backoff."""
    timeout = httpx.Timeout(settings.webhook_timeout_seconds)
    last_exc: BaseException | None = None
    for attempt in range(WEBHOOK_MAX_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                if 200 <= response.status_code < 300:
                    return True
                logger.warning(
                    "Webhook returned %s for %s (attempt %s/%s)",
                    response.status_code,
                    url,
                    attempt + 1,
                    WEBHOOK_MAX_ATTEMPTS,
                )
        except (httpx.HTTPError, OSError) as exc:
            last_exc = exc
            logger.warning(
                "Webhook request failed for %s (attempt %s/%s): %s",
                url,
                attempt + 1,
                WEBHOOK_MAX_ATTEMPTS,
                exc,
            )
        if attempt < WEBHOOK_MAX_ATTEMPTS - 1:
            delay = WEBHOOK_BACKOFF_BASE_SECONDS * (2**attempt)
            await asyncio.sleep(delay)
    if last_exc is not None:
        logger.error("Webhook gave up for %s after %s attempts", url, WEBHOOK_MAX_ATTEMPTS)
    return False
