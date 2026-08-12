# Retail Taxonomy Operations Platform

## Assessment-Aligned Submission Plan + Enterprise Evolution (v2)

**Reading order:** Part A is the binding coding-test plan. Part B is optional post-assessment evolution — keep it out of the public repo README (one-paragraph pointer at most).

---

# PLAN

<img width="1010" height="367" alt="image" src="https://github.com/user-attachments/assets/5710102e-0144-4082-85fb-88fc44faf300" />

  # FLOW:

<img width="1010" height="263" alt="image" src="https://github.com/user-attachments/assets/d6a27601-c7f3-47be-b409-45d38e286ab6" />

         
# Part A — Assessment submission (Exercises 1–3)

This part satisfies the PDF literally. Enterprise practice that would conflict with a grader (OIDC-only, soft-delete, protected `main`, AI workflow) lives in Part B only.

## A0. Assessment commitments (non-negotiable)

| PDF ask | Assessment commitment |
|---|---|
| Public GitHub repository | Publish a **public** repo with a root README a stranger can follow |
| Commit directly to `master` | Work on **`master`**; at least **one commit ending each** of BUILD, SHIP, RUN; **do not squash or rewrite history** |
| Preferred stack | **React + TypeScript**, **Python + FastAPI**, **PostgreSQL 16** |
| Schema + persist + seed | Four-table relational model; Compose installs/configures DB; `scripts/seed.py` loads `data/seed/taxonomy.csv` |
| REST API | CRUD on hierarchy models (unauthenticated in BUILD) |
| Web UI CRUD via API | React UI create/read/update/**hard delete** through the API |
| TDD + runnable tests | Unit, component, integration, acceptance with documented `make` targets |
| Build/deploy outside IDE | `docker compose` + `Makefile`; README also documents a non-Docker fallback |
| Logging | **structlog** JSON middleware added in RUN commits on Exercise 1 handlers |
| Auth | Added in **RUN**: UI username/password + API **Basic Auth**; OIDC/JWT/OAuth2 bonus only |
| Health | Unauthenticated `/health` + `/health/ready`; **Prometheus + Grafana** + `scripts/smoke_health.sh` |

**Assessment git policy:**

```text
public GitHub repo
└── master (no squash / no history rewrite)
    ├── BUILD: schema, seed, API CRUD, UI CRUD
    │     including at least one red → green → refactor feature sequence
    ├── SHIP: complete test pyramid, Makefile, Compose, CI
    └── RUN: structlog, Basic Auth + login, health + Prometheus/Grafana
```

Protected-`main` / PR workflow is Part B only and is **not** used for the history the grader reviews.

**Pinned runtime (stranger contract):**

| Piece | Version / tag |
|---|---|
| Python | 3.12 |
| Node | 20 LTS |
| PostgreSQL | 16 (`postgres:16-alpine`) |
| API image | `python:3.12-slim` |
| Web image | `node:20-alpine` (dev) / nginx static (optional) |

**Published ports:**

| Service | Host port |
|---|---|
| UI (Vite) | `5173` |
| API (uvicorn) | `8000` |
| Postgres | `5432` |
| Prometheus | `9090` |
| Grafana | `3000` |

---

## A1. Exercise 1 — BUILD

BUILD ships working unauthenticated CRUD. Do **not** add login, Basic Auth, logging middleware, or Prometheus in this exercise.

### A1.1 Domain interpretation (assessment framing)

The PDF states the hierarchy “uniquely identifies a SKU.” For the assessment:

- Treat each full path `Zone / Department / Category / SubCategory` as a **unique merchandise classification leaf** (SKU-class identity).
- Persist the four-level hierarchy so a leaf is uniquely addressable by path and by stable UUID.
- Allowed metadata: `id`, `description`, `created_at`, `updated_at` (as the PDF permits). **No `is_active` / soft-delete in the MVP.**
- Do **not** build a separate Product/SKU catalog unless time remains after CRUD works.

**Highlighted proposal:** PDF `Location` → model **`zones`**. Values (`Center`, `Perimeter`) are merchandising Area/Zone. Use table `zones`, FK `zone_id`, API `/api/v1/zones`, and UI label **Zone**. Seed CSV may keep the PDF column name `Location`; `scripts/seed.py` maps that column into `zones`. Document the PDF↔model mapping in `docs/assessment-notes.md`.

### A1.2 Relational schema (concrete)

Normalized four-table model. Parent delete is **CASCADE** (hard delete, matching the PDF CRUD ask).

```sql
-- Ship as Alembic migrations under apps/api/alembic/versions/

CREATE TABLE zones (
  id           UUID PRIMARY KEY,
  name         TEXT NOT NULL UNIQUE,
  description  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE departments (
  id           UUID PRIMARY KEY,
  zone_id      UUID NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  description  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (zone_id, name)
);

CREATE TABLE categories (
  id             UUID PRIMARY KEY,
  department_id  UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  description    TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (department_id, name)
);

CREATE TABLE subcategories (
  id           UUID PRIMARY KEY,
  category_id  UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  description  TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (category_id, name)
);

CREATE VIEW sku_classification_paths AS
SELECT
  s.id AS subcategory_id,
  z.name AS zone,
  d.name AS department,
  c.name AS category,
  s.name AS subcategory,
  z.name || ' > ' || d.name || ' > ' || c.name || ' > ' || s.name AS full_path
FROM subcategories s
JOIN categories c ON c.id = s.category_id
JOIN departments d ON d.id = c.department_id
JOIN zones z ON z.id = d.zone_id;
```

Soft-delete / retire is Part B only.

### A1.3 Seed data (must pass)

After reconstructing PDF line wraps, seed **must** produce:

| Entity | Count |
|---|---|
| Zones | 2 (`Center`, `Perimeter`) |
| Departments | 8 |
| Categories | 25 |
| Subcategories | 61 |
| Unique hierarchy paths | 61 |

Seed CSV may retain the PDF header/column name `Location`; the seed script maps that column into the `zones` table.

**PDF → CSV reconstruction rules** (document in `docs/assessment-notes.md`):

1. A data row starts with `Center,` or `Perimeter,`.
2. If the next line does **not** start with `Center,` / `Perimeter,` and is not a page artifact (`3.`) or header, **join it with a single space** onto the previous subcategory.
3. Only two wraps exist:
   - `Refrigerated English Muffins and` + `Biscuits`
   - `Refrigerated Sweet Breakfast Baked` + `Goods`
4. Drop PDF page markers (`3.` on pages 2–3).
5. **Source of truth for runtime is the canonical unwrapped file** `data/seed/taxonomy.csv`. Do not parse the PDF at startup. Tests assert counts + the two reconstructed names.

**Deliverables:**

- `data/seed/taxonomy.csv` (canonical, unwrapped)
- `scripts/seed.py` (idempotent upsert; copied into the API image at `/app/scripts/seed.py`)
- Integration test asserting 2 / 8 / 25 / 61 and the two wrapped names

**DB install / configure / populate:**

```bash
docker compose up -d postgres
docker compose run --rm api alembic upgrade head
docker compose run --rm api python /app/scripts/seed.py
# Makefile equivalent: make up && make seed
```

API Dockerfile `WORKDIR` is `/app`. Compose bind-mounts repo `scripts/` → `/app/scripts` (and `apps/api` → `/app`) so the seed path works in both live and one-shot containers.

### A1.4 REST API (CRUD surface)

Base path: `/api/v1`  
**BUILD auth:** none. Health routes are added in RUN but may exist as stubs; they must stay unauthenticated.  
Format: JSON, UUID ids, UTC ISO-8601, RFC 7807 `application/problem+json` on errors.

| Resource | Endpoints |
|---|---|
| Zones | `GET/POST /api/v1/zones`, `GET/PUT/DELETE /api/v1/zones/{id}` |
| Departments | `GET/POST /api/v1/zones/{zone_id}/departments`, `GET/PUT/DELETE /api/v1/departments/{id}` |
| Categories | `GET/POST /api/v1/departments/{department_id}/categories`, `GET/PUT/DELETE /api/v1/categories/{id}` |
| Subcategories | `GET/POST /api/v1/categories/{category_id}/subcategories`, `GET/PUT/DELETE /api/v1/subcategories/{id}` |
| Tree / paths | `GET /api/v1/taxonomy/tree`, `GET /api/v1/taxonomy/paths` |

OpenAPI served at `/openapi.json`.

**Contract examples** (same shape on all four resources):

`POST /api/v1/zones/{zone_id}/departments`

```json
{ "name": "Bakery", "description": "In-store bakery" }
```

`201` response:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "zone_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "name": "Bakery",
  "description": "In-store bakery",
  "created_at": "2026-08-11T05:00:00Z",
  "updated_at": "2026-08-11T05:00:00Z"
}
```

`GET` item → `200` same object. `GET` collection → `{ "items": [ ... ] }`.

`PUT` item:

```json
{ "name": "Bakery", "description": "Updated" }
```

`DELETE` item → `204 No Content`. Children are removed by **ON DELETE CASCADE**.

`409` duplicate sibling name:

```json
{
  "type": "https://example.com/problems/duplicate-name",
  "title": "Conflict",
  "status": 409,
  "detail": "A department named 'Bakery' already exists under this zone.",
  "instance": "/api/v1/zones/7c9e6679-7425-40de-944b-e07fc1f90ae7/departments"
}
```

`404` unknown id → problem+json `status: 404`. `422` validation → FastAPI/Pydantic problem body.

### A1.5 React UI (CRUD via API)

BUILD UI has **no login screen**.

- Hierarchy browser (tree or cascading lists): Zone → Department → Category → SubCategory.
- Detail panel: **Create / Edit / Delete** for the selected level, with delete confirmation.
- All reads/writes go through the REST API (Vite proxy; no browser→Postgres).
- Empty / error / loading states.

**Browser → API (locked):** Vite `server.proxy` in `apps/web/vite.config.ts`:

```ts
proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } }
```

Inside Compose, the web container proxies `/api` → `http://api:8000`. No CORS config required for the assessment path. Optional `VITE_API_BASE_URL` is unused unless someone disables the proxy.

### A1.6 BUILD acceptance (grader-facing)

- [ ] Postgres up via Compose; migrations applied; seed loads 61 unique paths
- [ ] Wrapped subcategory names intact
- [ ] REST CRUD works for all four levels, including hard delete + CASCADE
- [ ] React UI performs CRUD exclusively through the API (no auth yet)
- [ ] At least one feature shows red → green → refactor commits on `master`
- [ ] README documents how to run API + UI locally

---

## A2. Exercise 2 — SHIP

### A2.1 TDD practices and commit cadence

**Cadence (required):**

1. **During BUILD:** pick one feature (e.g. “cannot create duplicate sibling names”). Commit a failing test (`red`), then the implementation (`green`), then a small cleanup (`refactor`). Leave those commits unsquashed.
2. **During SHIP:** fill the rest of the pyramid, wire `make test*`, add CI. SHIP commits are tests + automation, not a rewrite of BUILD history.
3. **During RUN:** add auth-rejection tests in the same commits that introduce Basic Auth.

| Layer | Examples | Command |
|---|---|---|
| Unit | Uniqueness helpers, seed line-join, CASCADE documented in domain | `make test-unit` → `pytest apps/api/tests/unit` |
| Component | Tree/list, create/edit forms, delete confirm | `make test-component` → `npm --prefix apps/web test` (Vitest + Testing Library) |
| Integration | API + real Postgres 16 (Compose service `postgres`) | `make test-integration` → `pytest apps/api/tests/integration` |
| Acceptance | Browse → create → update → delete → verify via API | `make test-acceptance` |

Acceptance is **mandatory**, not optional:

```bash
npx --prefix apps/web playwright install --with-deps chromium
make test-acceptance
```

CI runs the same install before Playwright.

**Invariants (BUILD/SHIP):**

- No duplicate sibling names under the same parent (`409`)
- `DELETE` parent **cascades** children
- Seed is idempotent and asserts 2 / 8 / 25 / 61 + two wrap names

**Invariants (RUN commits):**

- Missing/invalid Basic Auth → `401` on `/api/v1/*` (except documented public routes)
- UI delete still calls `DELETE` and refreshes after login

### A2.2 Build and deploy outside the IDE

**Stranger runbook (root README):**

```bash
git clone <public-repo-url>
cd <repo>
cp .env.example .env
make up          # docker compose up --build -d
make seed
make test        # unit + component + integration
npx --prefix apps/web playwright install --with-deps chromium
make test-acceptance
open http://localhost:5173
curl -sS http://localhost:8000/health
curl -sS http://localhost:8000/health/ready
```

**`.env.example` (complete):**

```bash
POSTGRES_USER=taxonomy
POSTGRES_PASSWORD=taxonomy
POSTGRES_DB=taxonomy
DATABASE_URL=postgresql+psycopg://taxonomy:taxonomy@postgres:5432/taxonomy
# host-side API when not using Compose DNS:
# DATABASE_URL=postgresql+psycopg://taxonomy:taxonomy@localhost:5432/taxonomy
DEMO_USER=admin
DEMO_PASSWORD=password
```

`DEMO_*` are unused until RUN; ship them in `.env.example` from day one so RUN does not surprise a stranger.

**Makefile targets (all required):** `up`, `down`, `seed`, `logs`, `test`, `test-unit`, `test-component`, `test-integration`, `test-acceptance`.

**Required files:**

```text
docker-compose.yml
Makefile
.env.example
scripts/seed.py
.github/workflows/ci.yml
README.md
```

**CI:** `.github/workflows/ci.yml` runs on every push to `master`: lint + unit + component + integration against a Postgres 16 service. Playwright is a separate job that installs Chromium.

**Non-Docker fallback (README appendix):**

1. Install Python 3.12, Node 20, PostgreSQL 16.
2. Create DB/user matching `.env.example`.
3. `python3.12 -m venv .venv && source .venv/bin/activate`
4. `pip install -r apps/api/requirements.txt && cd apps/api && alembic upgrade head`
5. `python scripts/seed.py` (with `DATABASE_URL` pointing at localhost)
6. `uvicorn app.main:app --reload --port 8000` from `apps/api`
7. `cd apps/web && npm install && npm run dev` (Vite on `5173`, proxy `/api` → `8000`)

### A2.3 SHIP acceptance

- [ ] `make test` runs without IDE settings
- [ ] `make test-acceptance` documented and green after Playwright install
- [ ] `make up` brings up DB + API + UI on a clean machine with Docker
- [ ] Non-Docker appendix exists
- [ ] `.github/workflows/ci.yml` present
- [ ] Distinct `master` commits for SHIP (tests + scripts + CI)

---

## A3. Exercise 3 — RUN

RUN is **new commits on Exercise 1/2 code** after BUILD + SHIP already run without auth.

### A3.1 Logging framework

- API: **structlog** JSON to stdout.
- Add middleware + per-CRUD log events as diffs on BUILD handlers (visible in `git log` / `git show` on `master`).
- Fields: `service`, `level`, `event`, `request_id`, `user` (username only, after auth exists), `resource`, `resource_id`, `duration_ms`, `outcome`. Never log passwords or `Authorization` values.
- UI: `console` logs for failed API calls in a fixed `{ event, status, path }` shape.

### A3.2 Authentication (PDF-literal + bonus)

These commits change BUILD files:

| File (illustrative) | Change |
|---|---|
| `apps/api/.../auth.py` | HTTP Basic Auth dependency; `DEMO_USER` / `DEMO_PASSWORD` |
| `apps/api/.../routers/*.py` | Protect `/api/v1/*` except OpenAPI if desired |
| `apps/web/src/pages/Login.tsx` | Username/password form |
| `apps/web/src/api/client.ts` | Send `Authorization: Basic ...` after login (sessionStorage) |

| Surface | Mechanism |
|---|---|
| UI | Login form; demo `admin` / `password` from env |
| API | **HTTP Basic Auth** on `/api/v1/*` |

Public (no auth): `GET /health`, `GET /health/ready`.  
Optional authenticated: `GET /api/v1/health/details`.

Document demo credentials in README (assessment only).

**Bonus only:** OIDC and/or JWT/OAuth2 **in addition to** Basic Auth (flag or `docs/oidc-bonus.md`). Bonus must not replace Basic Auth.

### A3.3 Proactive health and monitoring (committed stack)

No forks. Ship all of the following:

| Path | Auth | Behavior |
|---|---|---|
| `GET /health` | none | Liveness: process up |
| `GET /health/ready` | none | Readiness: DB `SELECT 1` |
| `GET /api/v1/health/details` | Basic Auth | Operator diagnostics |

**Monitoring the candidate sets up:**

- Compose services: **Prometheus** (`:9090`) scrapes API `/metrics` (Prometheus client in FastAPI).
- **Grafana** (`:3000`) with checked-in datasource + one dashboard (`docs/grafana/dashboard.json`, provisioned from `docs/grafana/`).
- Compose `healthcheck` on `api` and `postgres`.
- `scripts/smoke_health.sh` curls **`/health` and `/health/ready` with no credentials** and exits non-zero on failure.

Proactive, not reactive: smoke script + Prometheus scrape + Grafana panel for request rate / latency / DB ready. README shows how to open Grafana and where the smoke script runs (`make smoke`).

### A3.4 RUN acceptance

- [ ] structlog present; CRUD requests emit JSON logs (shown as source diffs)
- [ ] UI login + API Basic Auth demonstrated; BUILD flows still work after login
- [ ] `/health` and `/health/ready` work without credentials
- [ ] Prometheus + Grafana up via Compose; `make smoke` passes
- [ ] Distinct `master` commit(s) for RUN

---

## A4. Assessment repository layout

```text
apps/
  api/                      # FastAPI, Alembic, domain, (RUN) Basic Auth + structlog + /metrics
  web/                      # React + TypeScript; vite.config.ts proxies /api
    vite.config.ts
data/seed/taxonomy.csv
scripts/seed.py             # copied/mounted to /app/scripts/seed.py
scripts/smoke_health.sh
tests/acceptance/           # Playwright
docs/
  assessment-notes.md       # SKU-path + PDF wrap rules
  grafana/
    datasource.yml
    dashboard.json
.github/workflows/ci.yml
docker-compose.yml          # postgres, api, web, prometheus, grafana
Makefile
.env.example
README.md                   # stranger runbook + non-Docker appendix
```

---

## A5. Assessment submission ready when

- Public repo on `master` with ≥1 commit per exercise and intact history
- At least one BUILD red → green → refactor sequence
- React + FastAPI + Postgres 16 via Compose; Vite proxies `/api`
- Seed → exactly 61 unique paths; wrapped names preserved
- Full CRUD UI via REST, including hard delete + CASCADE
- Unit / component / integration / acceptance tests documented and green
- CI workflow on `master`; non-Docker appendix present
- RUN: structlog, UI password + API Basic Auth, `/health` + `/health/ready`, Prometheus + Grafana, `make smoke`
- Root README: clone → up → seed → (after RUN: login) → CRUD → tests → health

---

## A6. Grader traceability matrix

| PDF section | Plan section | Primary artifacts |
|---|---|---|
| Public repo / `master` commits / no rewrite | A0 | Git history, public GitHub URL |
| React + Python + Postgres | A0, A4 | `apps/web`, `apps/api`, `postgres:16-alpine` |
| BUILD schema | A1.2 | Alembic DDL |
| BUILD persist + populate | A1.3 | Compose + `/app/scripts/seed.py` |
| BUILD REST API | A1.4 | FastAPI routers + JSON examples |
| BUILD UI CRUD | A1.5 | React pages; Vite proxy |
| SHIP TDD tests | A2.1 | pytest / Vitest / Playwright |
| SHIP outside-IDE deploy | A2.2 | Makefile, Compose, README, `.github/workflows/ci.yml` |
| RUN logging | A3.1 | structlog middleware (diff on BUILD handlers) |
| RUN auth | A3.2 | Basic Auth + login form (not in BUILD) |
| RUN health / monitoring | A3.3 | `/health`, `/health/ready`, Prometheus, Grafana, `smoke_health.sh` |

---

# Part B — Enterprise target state (after assessment)

Part B must **not** replace Part A in the submission. Implement only after Part A gates pass. In the public assessment repo, mention this as a one-paragraph “future state” at most.

## B1. Executive decision

Build a **Retail Taxonomy Operations Platform** on the Part A foundation.

Long-term target: React/TypeScript console; Python/FastAPI BFF+API+worker; PostgreSQL system of record; event-ready modular monolith; managed containers (ECS Fargate reference); IaC; OpenTelemetry; OpenAPI + transactional-outbox CloudEvents; assistive AI that proposes only.

## B2. Domain corrections (with assessment bridge)

| Source statement | Enterprise interpretation | Assessment bridge (Part A) |
|---|---|---|
| Hierarchy uniquely identifies a SKU | Classifies merchandise; future `product`/`sku` references taxonomy | Unique four-level path is SKU-class identity now |
| PDF `Location` | Merchandising Area/Zone | Model as `zones` / `zone_id` / `/api/v1/zones` / UI Zone; CSV may keep `Location` |
| CRUD includes delete | Soft-retire published/referenced master data | **Hard delete + CASCADE** in MVP |
| Username/password + API Basic Auth | Demo only; production OIDC + workload identity | **Ship Basic Auth + UI password in RUN**; OIDC bonus |
| Public repo; commit to master | Assessment-specific | Follow Part A git policy; enterprise uses protected `main` later |

## B3. CTO principles (post-MVP)

1. Business state before technology spectacle
2. Modular monolith first
3. Managed containers by default; Kubernetes only via staffed paved road or fleet-scale gate
4. Relational system of record; optimize hierarchy storage only after benchmarks miss SLOs
5. Governed releases (draft → validate → submit → approve → publish → retire) **after** MVP CRUD
6. BFF + OIDC Authorization Code + PKCE for humans; OAuth2 for machines
7. API and events, never shared databases
8. AI proposes; deterministic code decides
9. Approval is payload-bound
10. Open logical contracts; AWS as initial concrete cloud

## B4. Target architecture

```mermaid
flowchart TD
    U["Business operator"] --> EDGE["CDN + WAF"]
    EDGE --> WEB["React operations console"]
    WEB --> BFF["FastAPI BFF / API"]
    IDP["Enterprise IdP"] --> BFF
    BFF --> DB["Managed PostgreSQL"]
    BFF --> OBJ["Object storage"]
    BFF --> Q["Managed queue"]
    Q --> W["Async worker"]
    W --> DB
    DB --> O["Transactional outbox"]
    O --> BUS["Managed event bus + DLQ"]
    BUS --> EXT["PIM / ERP / POS / commerce / analytics"]
    BFF --> AI["Governed AI gateway"]
    AI --> TOOLS["Typed domain tools"]
    TOOLS --> BFF
    WEB --> OTEL["OpenTelemetry"]
    BFF --> OTEL
    W --> OTEL
```

| Unit | Responsibility |
|---|---|
| Web | Static React assets on CDN |
| BFF/API | Session, authz, commands/queries, audit |
| Worker | Imports/exports, outbox, AI evaluation jobs |
| PostgreSQL | Authoritative state, workflow, audit, outbox |

---

## B5. RUN foundation (enterprise)

### B5.1 Infrastructure

Terraform/OpenTofu: separate accounts, private networks, managed containers, RDS PostgreSQL Multi-AZ, object storage, queue, event bus, DLQ, secrets, KMS, observability, backups. AWS: CloudFront/WAF/S3, ECS Fargate, RDS, SQS/EventBridge.

### B5.2 Container standard

Multi-stage reproducible builds, non-root, read-only FS, probes, separate migration job, SBOM/signing, Compose for local parity, promote by digest.

### B5.3 Identity, authorization, audit

Roles: Viewer, Editor/Steward, Approver, Publisher, Administrator, Integration Service, Auditor. Federated OIDC + MFA; workload identity for CI; immutable audit distinct from business release history.

### B5.4 Health, telemetry, SRE

`/startupz`, `/livez`, `/readyz`, authenticated `/health/details`. OpenTelemetry. RED/USE dashboards, synthetics, SLO burn-rate alerts, runbooks. (Assessment uses `/health` + `/health/ready` + Prometheus/Grafana.)

### B5.5 Initial NFRs / SLOs

| Area | Initial target |
|---|---|
| Availability | 99.9% monthly authenticated UI/API |
| API latency | p95 reads ≤ 250 ms; writes ≤ 500 ms |
| Search | p95 ≤ 500 ms |
| Front-end | p75 LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 |
| Recovery | RPO ≤ 5 min; RTO ≤ 60 min |
| Accessibility | WCAG 2.2 AA critical flows |
| Auditability | 100% mutations/approvals/publications/AI tool calls attributable |

### B5.6 Resilience

Multi-AZ baseline; defer active-active multi-region. PITR, restore drills, timeouts/retries/idempotency, degrade without AI/integrations.

---

## B6. SHIP foundation (enterprise)

### B6.1 Repository (evolves from Part A)

```text
apps/web
apps/api
apps/worker
packages/design-system
packages/openapi-client
packages/domain-contracts
infra/terraform
deploy
tests/acceptance
docs/adr
docs/runbooks
```

### B6.2 CI quality gates

Format/lint/types/secrets; domain unit/property tests; component a11y; Postgres integration; OpenAPI contracts; Playwright; security tests; SAST/deps/IaC/container scans; signed artifacts. Nightly: DAST, performance, restore, AI evals when enabled.

### B6.3 CD and promotion

Protected `main` (post-assessment), signed artifacts, promote digest, expand/migrate/contract, progressive delivery, feature flags. **Do not rewrite assessment `master` history to invent this.**

---

## B7. BUILD evolution (enterprise product)

### B7.1 Domain model

`organization`, `taxonomy`, `taxonomy_level_definition`, `taxonomy_release`, `taxonomy_node`, `node_alias`, `change_set`/`change_item`, `approval`, `import_job`/`import_exception`, `export_job`, `audit_event`, `outbox_event`, future `product`/`sku`/`classification_assignment`.

Published releases immutable; editors work via change sets; optimistic concurrency; compensating rollback.

### B7.2 API evolution

Keep `/api/v1` CRUD as compatibility; add change-set, approve/publish, import/export job, impact preview, release compare. Cursor pagination, ETag/If-Match, Idempotency-Key, `202` for async.

### B7.3 Bulk ops and search

Template → signed upload → scan → map → dry-run → exceptions → apply to draft → approve/publish. Search starts in Postgres; OpenSearch only when measured need.

### B7.4 Premium operations UX

Taxonomy workbench: tree + table + inspector + activity. WCAG 2.2 AA. Soft-retire replaces casual hard delete for published data.

### B7.5 Integration

Transactional outbox → event bus → consumer queues/DLQ; CloudEvents; AsyncAPI; no shared DB.

### B7.6 Agentic AI (optional, post-MVP only)

**Out of scope for PDF grading.** Typed tools only; proposals never approve/publish/delete. Hard budgets, kill switch, evals. No AI-generated production SQL.

---

## B8. Phased roadmap

| Phase | Outcome | Maps to |
|---|---|---|
| **A — Assessment MVP** | Part A gates green; public repo grader-ready | Exercises 1–3 |
| 0. Decisions and runway | Glossary, threat model, NFRs, ADRs | Post-assessment |
| 1. Deterministic productize | Roles, concurrency, audit, cloud env | Evolution of BUILD/SHIP/RUN |
| 2. Production pilot | Managed runtime, full IdP, backup/restore | Enterprise RUN |
| 3. Governance and integration | Releases, outbox/events, first connector | Master-data utility |
| 4. Assistive AI pilot | Mapping/duplicates/summaries with evals | Optional |
| 5. Governed agent workflows | Human-approved proposals only | Optional |
| 6. Evidence-driven scale | Extract/optimize only on measured triggers | Optional |

---

## B9. Enterprise acceptance gates

- Seed still imports to 61 valid paths
- Authn/z on all actions; invariants enforced
- Impact preview before move/retire; payload-bound publish
- Audit attribution; import/export quality
- Probes, traces, metrics, synthetics, rollback, restore demonstrated
- AI cannot directly mutate/approve/publish/delete/execute SQL

---

## B10. Fitness functions, risks, deferred items

**Evolve when measured:** closure table / Redis / OpenSearch / Kubernetes / microservice / Kafka / vector DB / multi-region / expanded AI authority.

**Principal risks:** wrong SKU interpretation (bridged via Part A path identity); consumer breakages; concurrency; platform overkill; migration risk; event inconsistency; supply chain; audit leakage; AI abuse/cost; inaccessible UI.

**Deferred until gates fire:** microservices, active-active multi-region, service mesh, Kafka, Redis, dedicated graph/vector DB, OpenSearch, autonomous AI publication, free-form agent swarms, AI SQL, bespoke developer portal.

---

## B11. Ownership model

Product/domain team, taxonomy steward, platform, security, integration owners, AI governance. Assessment MVP may be a single full-stack owner.

---

## Final call

1. **Ship Part A literally** against the PDF, in exercise order: unauthenticated CRUD → tests/CI/Compose → logging + Basic Auth + Prometheus/Grafana.
2. **Keep Part B** as post-assessment modernization only.
3. Graders score Exercises 1–3. Architecture depth is upside only after those asks are met.
