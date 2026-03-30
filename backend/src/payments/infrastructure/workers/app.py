from __future__ import annotations

from core.infrastructure.messaging.consumer_app import build_rabbit_consumer_app
from core.settings import Settings
from faststream import FastStream
from payments.infrastructure.workers.handlers import register_payment_consumer


def build_consumer_app(settings: Settings) -> FastStream:
    return build_rabbit_consumer_app(settings, register_payment_consumer)
