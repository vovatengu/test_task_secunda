from __future__ import annotations

import asyncio
import logging
import signal
import sys

from core.logging import configure_logging
from core.settings import get_settings
from db.session import (
    async_session_factory,
    bind_session_maker,
    create_async_engine_from_settings,
    get_session_maker,
)
from payments.infrastructure.outbox_relay import run_outbox_relay

logger = logging.getLogger(__name__)


async def _async_main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_async_engine_from_settings(settings)
    bind_session_maker(async_session_factory(engine))
    stop = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            break

    try:
        await run_outbox_relay(stop, settings, get_session_maker())
    finally:
        await engine.dispose()


def main() -> None:
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        logger.info("Outbox relay stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
