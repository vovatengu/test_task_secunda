# Dev/test через compose и --env-file

DC_TEST = docker compose -f docker-compose.test.yml -p payment_processing_test --env-file=.env.test
DC_DEV  = docker compose -f docker-compose.dev.yml -p payment_processing --env-file=.env.dev

.PHONY: dev-up dev-down dev-restart dev-build dev-migrate dev-logs test-up test-down test-restart test-migrate structure

# --- DEV ---
dev-up:
	$(DC_DEV) up --build -d

dev-down:
	$(DC_DEV) down

dev-restart:
	$(DC_DEV) restart

dev-build:
	$(DC_DEV) build

dev-migrate:
	$(DC_DEV) exec app bash -c "alembic upgrade head"

dev-logs:
	$(DC_DEV) logs -f app consumer

# --- TEST ---
test-up:
	$(DC_TEST) up --build -d

test-down:
	$(DC_TEST) down -v

test-restart:
	$(DC_TEST) restart

test-migrate:
	$(DC_TEST) exec app bash -c "alembic upgrade head"

