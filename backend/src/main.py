from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.logging import configure_logging
from core.settings import get_settings
from db.session import async_session_factory, bind_session_maker, create_async_engine_from_settings
from payments.api.router import router as payments_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app
    settings = get_settings()
    configure_logging(settings.log_level)
    engine = create_async_engine_from_settings(settings)
    bind_session_maker(async_session_factory(engine))
    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(payments_router)
    return app


app = create_app()
