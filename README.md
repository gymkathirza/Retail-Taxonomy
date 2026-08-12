# Retail Taxonomy Operations Platform

Public assessment package for the Full Stack coding test (React + TypeScript + FastAPI + PostgreSQL 16).

Part A only: zones hierarchy, soft-delete CRUD, Compose stranger runbook, Basic Auth (RUN), health + Prometheus/Grafana.

## Stranger quick start (Docker)

```bash
git clone <public-repo-url>
cd Retail-Taxonomy
cp .env.example .env
make up          # docker compose up --build -d
make seed
make test        # unit + component + integration
npm install
npx playwright install --with-deps chromium
make test-acceptance
open http://localhost:5173
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/health/ready
make smoke
```

| Surface | URL |
|---|---|
| UI | http://localhost:5173 |
| API / OpenAPI | http://localhost:8000 / http://localhost:8000/openapi.json |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin / admin unless overridden) |

**Demo login (after RUN auth):** username `admin`, password `password` (from `.env.example`).

## Makefile targets

| Target | Purpose |
|---|---|
| `make up` | Build and start Compose stack |
| `make down` | Stop Compose |
| `make seed` | Alembic migrate + idempotent CSV seed |
| `make logs` | Follow Compose logs |
| `make test` | Unit + component + integration |
| `make test-unit` | pytest unit helpers |
| `make test-component` | Vitest + Testing Library |
| `make test-integration` | API + Postgres 16 in Compose |
| `make test-acceptance` | Playwright browse→CRUD→retire→restore |
| `make smoke` | Curl `/health` and `/health/ready` without credentials |

## Hierarchy model

PDF **Location** → DB/API/UI **`zones`**. Levels: Zone → Department → Category → Subcategory.

Soft-delete: `DELETE` retires a node and descendants (`is_active=false`); `POST .../restore` restores that node only. See `docs/assessment-notes.md`.

## Appendix: run without Docker

1. Install Python 3.12, Node 20, and PostgreSQL 16.
2. Create DB/user matching `.env.example` (`taxonomy` / `taxonomy` / `taxonomy`).
3. `cp .env.example .env` and set host `DATABASE_URL` to `postgresql+psycopg://taxonomy:taxonomy@localhost:5432/taxonomy`.
4. `python3.12 -m venv apps/api/.venv && source apps/api/.venv/bin/activate`
5. `pip install -r apps/api/requirements.txt`
6. `cd apps/api && alembic upgrade head`
7. `TAXONOMY_SEED_CSV=../../data/seed/taxonomy.csv PYTHONPATH=. python ../../scripts/seed.py`
8. From `apps/api`: `uvicorn app.main:app --reload --port 8000`
9. From `apps/web`: `npm install && npm run dev` (Vite on `5173`, proxies `/api` → `8000`)

## Assessment docs

- Plan: `Plan version 1/Retail-Taxonomy-Assessment-Aligned-Proposal.md`
- TDD milestones: `Plan version 1/Implementation-Plan-TDD-Milestones.md`
- Notes: `docs/assessment-notes.md`
