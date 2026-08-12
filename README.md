# Retail Taxonomy Operations Platform

A four-level retail merchandise taxonomy (**Zone → Department → Category → SubCategory**)
with a FastAPI + PostgreSQL backend and a React + TypeScript console. Implements the
**BUILD** scope of the assessment plan: relational schema, seed data, unauthenticated
REST CRUD with soft-delete/restore, and a web UI that performs all operations through
the API.

See [`Plan version 1/Retail-Taxonomy-Assessment-Aligned-Proposal.md`](Plan%20version%201/Retail-Taxonomy-Assessment-Aligned-Proposal.md)
for the full plan (BUILD / SHIP / RUN) and [`docs/assessment-notes.md`](docs/assessment-notes.md)
for domain mapping notes.

## Stack

| Piece | Version |
| --- | --- |
| Python | 3.12 |
| Node | 20 LTS |
| PostgreSQL | 16 |
| API | FastAPI + SQLAlchemy + Alembic |
| Web | React + TypeScript + Vite |

Ports: UI `5173`, API `8000`, Postgres `5432`.

## Quick start (Docker)

Prerequisites: Docker Engine + the Docker Compose plugin (`docker compose version`) and `make`.

```bash
git clone https://github.com/gymkathirza/Retail-Taxonomy.git
cd Retail-Taxonomy
cp .env.example .env
make up            # build + start postgres, api, web
make migrate       # apply Alembic migrations
make seed          # load data/seed/taxonomy.csv (2 / 8 / 25 / 61)
make test          # backend unit + integration tests
# Open the UI and check the API:
#   UI:  http://localhost:5173
#   API: http://localhost:8000/docs   (health: /health, /health/ready)
```

Stop everything with `make down`.

## Local development (no Docker)

```bash
git clone https://github.com/gymkathirza/Retail-Taxonomy.git
cd Retail-Taxonomy
```

1. Install Python 3.12, Node 20, and PostgreSQL 16.
2. Create the role/database from `.env.example`:
   ```bash
   createuser taxonomy --login --pwprompt   # password: taxonomy
   createdb -O taxonomy taxonomy
   ```
3. Backend:
   ```bash
   python3.12 -m venv .venv && source .venv/bin/activate
   pip install -r apps/api/requirements.txt
   export DATABASE_URL=postgresql+psycopg://taxonomy:taxonomy@localhost:5432/taxonomy
   (cd apps/api && alembic upgrade head)
   python scripts/seed.py
   (cd apps/api && uvicorn app.main:app --reload --port 8000)
   ```
4. Frontend (separate shell):
   ```bash
   cd apps/web && npm install && npm run dev   # Vite on :5173, proxies /api -> :8000
   ```

## REST API

Base path `/api/v1`. OpenAPI at `/openapi.json`, interactive docs at `/docs`.

- Zones: `GET/POST /zones`, `GET/PUT/DELETE /zones/{id}`, `POST /zones/{id}/restore`
- Departments: `GET/POST /zones/{zone_id}/departments`, `GET/PUT/DELETE /departments/{id}`, `POST /departments/{id}/restore`
- Categories: `GET/POST /departments/{department_id}/categories`, `GET/PUT/DELETE /categories/{id}`, `POST /categories/{id}/restore`
- Subcategories: `GET/POST /categories/{category_id}/subcategories`, `GET/PUT/DELETE /subcategories/{id}`, `POST /subcategories/{id}/restore`
- Tree/paths: `GET /taxonomy/tree`, `GET /taxonomy/paths`
- Health: `GET /health`, `GET /health/ready`

Behavior: `DELETE` soft-deletes the node **and all descendants** (idempotent `204`);
lists/tree/paths are active-only unless `?include_inactive=true`; `GET` by id returns
inactive rows; duplicate sibling names return `409`; restoring a child whose parent is
inactive returns `409`. Errors use `application/problem+json` (RFC 7807).

## Tests

```bash
# with Docker:
make test
# locally (venv active, DATABASE_URL set, DB migrated):
cd apps/api && python -m pytest
# frontend type-check + build:
cd apps/web && npm run build
```

## Cloud Agent environment

`.cursor/environment.json` provisions this repo for Cursor Cloud Agents without Docker:
`scripts/cloud/install.sh` installs PostgreSQL 16 + Python/Node dependencies, and
`scripts/cloud/start.sh` starts PostgreSQL, applies migrations, and seeds. The `api`
and `web` dev servers run as named terminals.

## Scope

This repo currently implements **Part A / Exercise 1 (BUILD)**. Logging (structlog),
authentication (Basic Auth + login), and monitoring (Prometheus/Grafana) are the
**RUN** exercise and are documented as future work in the plan.
