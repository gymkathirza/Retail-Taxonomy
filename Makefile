.PHONY: up down seed logs test test-unit test-component test-integration test-acceptance smoke perf

export DATABASE_URL ?= postgresql+psycopg://taxonomy:taxonomy@127.0.0.1:5432/taxonomy
API_VENV := apps/api/.venv/bin

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
	@if [ -x "$(API_VENV)/pytest" ]; then \
		cd apps/api && PYTHONPATH=. .venv/bin/pytest tests/unit -v; \
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
	npx playwright test --config=playwright.config.ts

smoke:
	@bash scripts/smoke_health.sh

perf: ## Run the Locust load test headless (override HOST/USERS/RATE/TIME)
	pip install -q -r perf/requirements.txt
	bash perf/run_perf.sh
