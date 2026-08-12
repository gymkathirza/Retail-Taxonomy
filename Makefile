.PHONY: up down seed logs test test-unit test-component test-integration test-acceptance smoke

export DATABASE_URL ?= postgresql+psycopg://taxonomy:taxonomy@127.0.0.1:5432/taxonomy
API_VENV := apps/api/.venv/bin
PYTEST := $(API_VENV)/pytest

up:
	docker compose up --build -d

down:
	docker compose down

seed:
	docker compose run --rm api alembic upgrade head
	docker compose run --rm api python /app/scripts/seed.py

logs:
	docker compose logs -f

test: test-unit test-component test-integration

test-unit:
	@if [ -x "$(PYTEST)" ]; then \
		cd apps/api && PYTHONPATH=. ../.venv/bin/pytest tests/unit -v || PYTHONPATH=. .venv/bin/pytest tests/unit -v; \
	else \
		docker compose run --rm -e PYTHONPATH=/app api pytest /app/tests/unit -v; \
	fi

test-component:
	npm --prefix apps/web test

test-integration:
	docker compose run --rm \
		-e PYTHONPATH=/app \
		-e DATABASE_URL=postgresql+psycopg://taxonomy:taxonomy@postgres:5432/taxonomy \
		api pytest /app/tests/integration -v

test-acceptance:
	@echo "wire in M5: Playwright acceptance"

smoke:
	@echo "wire in M8: scripts/smoke_health.sh"
