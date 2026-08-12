# Retail Taxonomy Assessment MVP — Implementation Plan (TDD)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:test-driven-development` on every behavior change. Prefer `superpowers:subagent-driven-development` or `superpowers:executing-plans` task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Part A (Exercises 1–3) as a stranger-runnable Compose package: zones hierarchy, FastAPI CRUD with soft-delete, React UI via API proxy, full test pyramid, then RUN (structlog, Basic Auth, health, Prometheus/Grafana).

**Architecture:** Modular monolith in one repo. `apps/api` (FastAPI + Alembic + Postgres 16) owns persistence and REST. `apps/web` (React + TS + Vite) proxies `/api` to the API. Compose installs/configures/populates DB; Makefile is the stranger CLI. Soft-delete via `is_active`; PDF `Location` → `zones`.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy/Alembic, psycopg, pytest, React 18+, TypeScript, Vite, Vitest, Testing Library, Playwright, PostgreSQL 16, Docker Compose, Prometheus, Grafana, structlog.

## Global Constraints

- Modify files only under `/Users/kathiresanmoorthy/Learning Playground/` (this repo: `Retail-Taxonomy`).
- Binding spec: `Plan version 1/Retail-Taxonomy-Assessment-Aligned-Proposal.md` Part A only. **Do not implement Part B.**
- **No OIDC/JWT/OAuth2 bonus** in the first delivery (Basic Auth + UI password only). Document as follow-up if time remains.
- PDF `Location` → DB/API/UI **`zones`**. Seed CSV may keep column `Location`.
- Soft-delete: `is_active`; `DELETE` retires node + descendants; `POST .../restore` node-only; no hard purge.
- BUILD has **no auth**. Auth/logging/metrics land only in **RUN** commits.
- TDD iron law: **failing test first**, then minimal code, then refactor. Commit after each green milestone (and red→green→refactor for the flagged BUILD feature).
- Git: work on branch `implement-assessment-mvp`, open PR to `main`. **Do not squash** on merge (preserve BUILD/SHIP/RUN history for graders). At least one commit ending each of BUILD, SHIP, RUN.
- Pinned: Python 3.12 (container), Node 20 (container), Postgres 16. Host may differ; Compose is source of truth.
- Ports: UI 5173, API 8000, Postgres 5432, Prometheus 9090, Grafana 3000.

## Assumptions (auto-approved — no blocking questions)

1. Implement **Part A only**; Part B stays documentation.
2. Skip OIDC/JWT bonus unless BUILD+SHIP+RUN core is done early.
3. Branch + PR to `main` (user request); merge without squash to honor PDF history policy.
4. Demo credentials `admin` / `password` from `.env.example`.
5. Seed reconstructed offline into `data/seed/taxonomy.csv` (counts 2/8/25/61).

## Nothing else needed from you

Proceeding with the above. If you return mid-flight and want OIDC bonus or direct-to-`main` commits (no PR), say so and we adjust.

---

## File map (create)

```text
apps/api/
  app/main.py, config.py, db.py, models.py, schemas.py, auth.py (RUN)
  app/routers/{zones,departments,categories,subcategories,taxonomy,health}.py
  app/services/{soft_delete,seed_helpers}.py
  alembic/ + alembic.ini
  requirements.txt, Dockerfile
  tests/unit/ tests/integration/
apps/web/
  package.json, vite.config.ts, tsconfig.json, index.html
  src/{main.tsx,App.tsx,api/client.ts,pages/*,components/*}
  src/**/*.test.tsx
  Dockerfile
data/seed/taxonomy.csv
scripts/seed.py, scripts/smoke_health.sh
tests/acceptance/
docs/assessment-notes.md
docs/grafana/{datasource.yml,dashboard.json}
docker-compose.yml, Makefile, .env.example, .gitignore
.github/workflows/ci.yml
README.md
```

---

## Milestone M0 — Repo scaffold (SHIP-early skeleton)

**Commit message:** `chore: scaffold Compose, Makefile, and app package layout`

- [ ] Create `.gitignore`, `.env.example`, `docker-compose.yml` (postgres only first), `Makefile` stubs, root `README.md` stranger stub
- [ ] Create `apps/api` and `apps/web` empty package skeletons
- [ ] Verify: `docker compose config` succeeds
- [ ] Commit

---

## Milestone M1 — Domain helpers (BUILD, TDD)

**Feature for red→green→refactor history:** sibling uniqueness (including inactive names).

### M1a — RED: uniqueness helper

- [ ] Write failing unit test: `apps/api/tests/unit/test_uniqueness.py` — duplicate sibling name under same parent is not allowed (active or inactive)
- [ ] Run: `pytest apps/api/tests/unit/test_uniqueness.py -v` → expect FAIL
- [ ] Commit: `test: fail uniqueness helper for duplicate sibling names`

### M1b — GREEN + refactor

- [ ] Minimal `app/services/uniqueness.py` to pass
- [ ] Run tests → PASS
- [ ] Small refactor if needed; tests stay green
- [ ] Commit: `feat: enforce sibling uniqueness including inactive names`

### M1c — Seed line-join + soft-delete walk (unit)

- [ ] RED then GREEN: seed wrap join for the two PDF wrapped names
- [ ] RED then GREEN: soft-delete marks node + descendants inactive
- [ ] Commits per cycle

---

## Milestone M2 — Schema + migrate + seed (BUILD)

- [ ] RED integration: after migrate+seed, counts 2/8/25/61 and wrap names (will fail until schema/seed exist)
- [ ] Alembic migration: `zones`, `departments`, `categories`, `subcategories` with `is_active`, `ON DELETE RESTRICT`, uniques
- [ ] `data/seed/taxonomy.csv` + `scripts/seed.py` (map `Location` → zones; all `is_active=true`)
- [ ] Compose postgres + `make seed` path
- [ ] GREEN integration seed test
- [ ] Commit: `feat: add zones hierarchy schema, migrations, and seed`

---

## Milestone M3 — REST CRUD API (BUILD, TDD)

Order per resource (zones first, then departments, categories, subcategories):

- [ ] RED integration: create/list/get/update/soft-delete/restore + `include_inactive`
- [ ] GREEN: FastAPI routers + schemas
- [ ] Tree/paths endpoints
- [ ] problem+json for 404/409/422
- [ ] Commit(s): `feat: add FastAPI CRUD for zones hierarchy with soft-delete`

**BUILD ending commit** should leave API working unauthenticated.

---

## Milestone M4 — React UI CRUD via API (BUILD)

- [ ] RED component tests: tree/detail, retire confirm, show-inactive, restore
- [ ] GREEN: Vite app, proxy `/api`, hierarchy browser + forms
- [ ] Compose `web` service
- [ ] Commit: `feat: add React taxonomy UI CRUD through API proxy`
- [ ] **BUILD milestone commit** if not already: ensure ≥1 BUILD-ending commit message clear

---

## Milestone M5 — SHIP: pyramid + automation + CI

- [ ] Wire `make test-unit|test-component|test-integration|test-acceptance|test`
- [ ] Playwright acceptance: browse → create → update → retire → restore
- [ ] `.github/workflows/ci.yml`
- [ ] README stranger runbook + non-Docker appendix
- [ ] `docs/assessment-notes.md` (Location→zones, wraps, soft-delete)
- [ ] Commit: `test: complete SHIP pyramid, Makefile targets, and CI`
- [ ] **SHIP ending commit**

---

## Milestone M6 — RUN: logging

- [ ] RED: assert structlog JSON fields on a CRUD request (caplog or log capture)
- [ ] GREEN: middleware + handler events; UI console shape for failures
- [ ] Commit: `feat: add structlog JSON logging to API CRUD path`

---

## Milestone M7 — RUN: Basic Auth + UI login

- [ ] RED: unauthenticated `/api/v1/*` → 401; health still 200
- [ ] GREEN: Basic Auth dependency; Login page; client sends Basic header
- [ ] Acceptance updated for login
- [ ] Commit: `feat: add UI login and API Basic Auth`

---

## Milestone M8 — RUN: health + Prometheus + Grafana

- [ ] `/health`, `/health/ready`, `/api/v1/health/details`, `/metrics`
- [ ] Compose prometheus + grafana + provisioned dashboard
- [ ] `scripts/smoke_health.sh` + `make smoke`
- [ ] Commit: `feat: add health probes, Prometheus, Grafana, and smoke script`
- [ ] **RUN ending commit**

---

## Milestone M9 — Push + PR

- [ ] Push `implement-assessment-mvp`
- [ ] Open PR to `main` with summary + test plan
- [ ] Note: merge **without squash** to preserve exercise history

---

## Commit cadence (summary)

| Milestone | Exercise | Example commits |
|---|---|---|
| M0 | chore | scaffold |
| M1 | BUILD TDD | red uniqueness → green uniqueness → helpers |
| M2–M4 | BUILD | schema/seed → API → UI |
| M5 | SHIP | tests + Makefile + CI |
| M6–M8 | RUN | logging → auth → health/monitoring |
| M9 | delivery | push + PR |

---

## Out of scope (this PR)

- Part B enterprise (OIDC primary, workers, outbox, AI, Terraform)
- OIDC/JWT/OAuth2 bonus (unless core complete early)
- Hard purge / physical CASCADE delete
- Product/SKU catalog
- Changes outside `Learning Playground/`
