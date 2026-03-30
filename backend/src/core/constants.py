API_V1_PREFIX = "/api/v1"

# RabbitMQ: payments pipeline (topic exchange → queue; failed processing → DLQ)
PAYMENTS_EXCHANGE = "payments.events"
PAYMENTS_ROUTING_KEY = "payments.new"
PAYMENTS_QUEUE_NAME = "payments.new"
PAYMENTS_DLX = "payments.dlx"
PAYMENTS_DLQ = "payments.new.dlq"
PAYMENTS_DLQ_ROUTING_KEY = "payments.new.dlq"

RETRY_COUNT_HEADER = "x-retry-count"
MAX_PAYMENT_PROCESS_ATTEMPTS = 3

WEBHOOK_MAX_ATTEMPTS = 3
WEBHOOK_BACKOFF_BASE_SECONDS = 1.0
