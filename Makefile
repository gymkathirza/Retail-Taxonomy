.PHONY: up down seed logs test test-unit test-component test-integration test-acceptance smoke

up:
	docker compose up --build -d

down:
	docker compose down

seed:
	@echo "seed target will run scripts/seed.py once the API image exists (M2)"

logs:
	docker compose logs -f

test: test-unit test-component test-integration

test-unit:
	@echo "wire in M1/M5: pytest apps/api/tests/unit"

test-component:
	@echo "wire in M4/M5: npm --prefix apps/web test"

test-integration:
	@echo "wire in M2/M5: pytest apps/api/tests/integration"

test-acceptance:
	@echo "wire in M5: Playwright acceptance"

smoke:
	@echo "wire in M8: scripts/smoke_health.sh"
