SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: up down seed logs test test-unit test-integration test-component migrate perf

up: ## Build and start postgres + api + web
	$(COMPOSE) up --build -d

down: ## Stop all services
	$(COMPOSE) down

migrate: ## Apply database migrations
	$(COMPOSE) run --rm api alembic upgrade head

seed: ## Load the canonical taxonomy seed (idempotent)
	$(COMPOSE) run --rm api python /app/scripts/seed.py

logs: ## Tail service logs
	$(COMPOSE) logs -f

test: test-unit test-integration ## Run backend unit + integration tests

test-unit: ## Backend unit tests
	$(COMPOSE) run --rm api python -m pytest tests/unit

test-integration: ## Backend integration tests (API + Postgres)
	$(COMPOSE) run --rm api python -m pytest tests/integration

test-component: ## Frontend component/type checks
	cd apps/web && npm run build

perf: ## Run the Locust load test headless (override HOST/USERS/RATE/TIME)
	pip install -q -r perf/requirements.txt
	bash perf/run_perf.sh
