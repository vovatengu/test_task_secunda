from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.logging import configure_logging
from core.settings import get_settings
from db.session import (
    async_session_factory,
    bind_session_maker,
    create_async_engine_from_settings,
    get_session_maker,
)
from payments.api.router import router as payments_router
from payments.infrastructure.outbox_relay import run_outbox_relay

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_async_engine_from_settings(settings)
    bind_session_maker(async_session_factory(engine))
    stop_relay = asyncio.Event()
    relay_task = asyncio.create_task(run_outbox_relay(stop_relay, settings, get_session_maker()))
    try:
        yield
    finally:
        stop_relay.set()
        try:
            await relay_task
        except Exception:
            logger.exception("Outbox relay task ended with an error")
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(payments_router)
    return app


app = create_app()
