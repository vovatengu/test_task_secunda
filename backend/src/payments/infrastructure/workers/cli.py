from __future__ import annotations

import asyncio
import logging
import sys

from core.logging import configure_logging
from core.settings import get_settings
from db.session import async_session_factory, bind_session_maker, create_async_engine_from_settings
from payments.infrastructure.workers.app import build_consumer_app


async def _async_main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_async_engine_from_settings(settings)
    bind_session_maker(async_session_factory(engine))
    app = build_consumer_app(settings)
    try:
        await app.run()
    finally:
        await engine.dispose()


def main() -> None:
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Consumer stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
