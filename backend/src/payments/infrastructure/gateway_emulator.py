from __future__ import annotations

import asyncio
import logging
import random

from core.settings import Settings

logger = logging.getLogger(__name__)


async def emulate_payment_gateway(settings: Settings) -> bool:
    """Sleep 2–5s (configurable), then succeed with configurable probability (default 90%)."""
    low = settings.gateway_delay_min_seconds
    high = settings.gateway_delay_max_seconds
    delay = random.uniform(low, high)
    await asyncio.sleep(delay)
    ok = random.random() < settings.gateway_success_probability
    if not ok:
        logger.info("Gateway emulation: declined after %.2fs", delay)
    return ok
