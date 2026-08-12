# Retail Taxonomy Operations Platform

## Assessment-Aligned Submission Plan + Enterprise Evolution (v2)

**Reading order:** Part A is the binding coding-test plan. Part B is optional post-assessment evolution — keep it out of the public repo README (one-paragraph pointer at most).

**Implementation:** TDD milestone plan → [`Implementation-Plan-TDD-Milestones.md`](./Implementation-Plan-TDD-Milestones.md). Delivery branch `implement-assessment-mvp` → PR into `main` (**merge without squash** so BUILD/SHIP/RUN history stays grader-visible).

---

# PLAN

<img width="1010" height="367" alt="image" src="https://github.com/user-attachments/assets/5710102e-0144-4082-85fb-88fc44faf300" />

  # FLOW:

<img width="1010" height="263" alt="image" src="https://github.com/user-attachments/assets/d6a27601-c7f3-47be-b409-45d38e286ab6" />

         
# Part A — Assessment submission (Exercises 1–3)

This part satisfies the PDF literally. Enterprise practice that would conflict with a grader (OIDC-only, protected `main`, AI workflow) lives in Part B only. Soft-delete (`is_active`) is **in Part A** — HTTP DELETE retires nodes; hard purge stays out of scope.

## A0. Assessment commitments (non-negotiable)

| PDF ask | Assessment commitment |
|---|---|
| Public GitHub repository | Publish a **public** repo with a root README a stranger can follow |
| Commit directly to `master` | Work on **`master`**; at least **one commit ending each** of BUILD, SHIP, RUN; **do not squash or rewrite history** |
| Preferred stack | **React + TypeScript**, **Python + FastAPI**, **PostgreSQL 16** |
| Schema + persist + seed | Four-table relational model; Compose installs/configures DB; `scripts/seed.py` loads `data/seed/taxonomy.csv` |
| REST API | CRUD on hierarchy models (unauthenticated in BUILD) |
| Web UI CRUD via API | React UI create/read/update/**soft-delete (retire)** through the API |
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
- Allowed metadata: `id`, `description`, `is_active`, `created_at`, `updated_at` (as the PDF permits, plus soft-delete flag).
- Do **not** build a separate Product/SKU catalog unless time remains after CRUD works.

**Highlighted proposal:** PDF `Location` → model **`zones`**. Values (`Center`, `Perimeter`) are merchandising Area/Zone. Use table `zones`, FK `zone_id`, API `/api/v1/zones`, and UI label **Zone**. Seed CSV may keep the PDF column name `Location`; `scripts/seed.py` maps that column into `zones`. Document the PDF↔model mapping in `docs/assessment-notes.md`.

**Highlighted proposal (soft-delete):** HTTP `DELETE` = soft-delete via `is_active BOOLEAN NOT NULL DEFAULT true` on `zones`, `departments`, `categories`, and `subcategories`. `DELETE` sets `is_active=false` on the node **and all descendants** in one transaction; idempotent `204` if already inactive. FKs are `ON DELETE RESTRICT` (no physical CASCADE wipe). Hard purge is out of scope.

### A1.2 Relational schema (concrete)

Normalized four-table model. Soft-delete via `is_active`; FKs are **`ON DELETE RESTRICT`** (no physical CASCADE wipe). Hard purge is out of scope.

```sql
-- Ship as Alembic migrations under apps/api/alembic/versions/

CREATE TABLE zones (
  id           UUID PRIMARY KEY,
  name         TEXT NOT NULL UNIQUE,
  description  TEXT,
  is_active    BOOLEAN NOT NULL DEFAULT true,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE departments (
  id           UUID PRIMARY KEY,
  zone_id      UUID NOT NULL REFERENCES zones(id) ON DELETE RESTRICT,
  name         TEXT NOT NULL,
  description  TEXT,
  is_active    BOOLEAN NOT NULL DEFAULT true,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (zone_id, name)
);

CREATE TABLE categories (
  id             UUID PRIMARY KEY,
  department_id  UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
  name           TEXT NOT NULL,
  description    TEXT,
  is_active      BOOLEAN NOT NULL DEFAULT true,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (department_id, name)
);

CREATE TABLE subcategories (
  id           UUID PRIMARY KEY,
  category_id  UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
  name         TEXT NOT NULL,
  description  TEXT,
  is_active    BOOLEAN NOT NULL DEFAULT true,
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
  z.name || ' > ' || d.name || ' > ' || c.name || ' > ' || s.name AS full_path,
  s.is_active AS is_active
FROM subcategories s
JOIN categories c ON c.id = s.category_id
JOIN departments d ON d.id = c.department_id
JOIN zones z ON z.id = d.zone_id;
```

Uniqueness includes inactive names (`UNIQUE` still applies after soft-delete). Recreating a retired sibling name → `409`. Restore is explicit (see A1.4).

### A1.3 Seed data (must pass)

After reconstructing PDF line wraps, seed **must** produce:

| Entity | Count |
|---|---|
| Zones | 2 (`Center`, `Perimeter`) |
| Departments | 8 |
| Categories | 25 |
| Subcategories | 61 |
| Unique hierarchy paths | 61 |

Seed CSV may retain the PDF header/column name `Location`; the seed script maps that column into the `zones` table. **Seed all rows with `is_active=true`.**

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
| Zones | `GET/POST /api/v1/zones`, `GET/PUT/DELETE /api/v1/zones/{id}`, `POST /api/v1/zones/{id}/restore` |
| Departments | `GET/POST /api/v1/zones/{zone_id}/departments`, `GET/PUT/DELETE /api/v1/departments/{id}`, `POST /api/v1/departments/{id}/restore` |
| Categories | `GET/POST /api/v1/departments/{department_id}/categories`, `GET/PUT/DELETE /api/v1/categories/{id}`, `POST /api/v1/categories/{id}/restore` |
| Subcategories | `GET/POST /api/v1/categories/{category_id}/subcategories`, `GET/PUT/DELETE /api/v1/subcategories/{id}`, `POST /api/v1/subcategories/{id}/restore` |
| Tree / paths | `GET /api/v1/taxonomy/tree`, `GET /api/v1/taxonomy/paths` |

OpenAPI served at `/openapi.json`.

**Soft-delete / list / restore contract:**

- `DELETE /api/v1/{resource}/{id}` sets `is_active=false` on the node **and all descendants** in one transaction → `204 No Content`. Idempotent: already inactive → still `204`.
- FKs remain `ON DELETE RESTRICT`; rows are not physically deleted. Hard purge is out of scope.
- `GET` lists, tree, and paths default to **active-only**. Pass `?include_inactive=true` to include retired nodes.
- `GET` by id returns the row even when inactive (`200` with `"is_active": false`).
- Uniqueness includes inactive names → recreating a retired sibling name → `409`.
- `POST /api/v1/{resource}/{id}/restore` restores **the node only** (`is_active=true`). Restoring a child whose parent is inactive → `409`. Descendants stay inactive until restored individually.

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
  "is_active": true,
  "created_at": "2026-08-11T05:00:00Z",
  "updated_at": "2026-08-11T05:00:00Z"
}
```

`GET` item → `200` same object (including inactive). `GET` collection → `{ "items": [ ... ] }` (active-only unless `?include_inactive=true`).

`PUT` item:

```json
{ "name": "Bakery", "description": "Updated" }
```

`DELETE` item → `204 No Content` (soft-delete: node + descendants `is_active=false` in one transaction; idempotent if already inactive).

`POST .../restore` → `200` with the restored object (`"is_active": true`). Child restore with inactive parent → `409`.

`409` duplicate sibling name (active or inactive):

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
- Detail panel: **Create / Edit / Retire (soft-delete) / Restore** for the selected level.
- **Retire confirmation** before calling `DELETE` (soft-delete).
- **Show inactive** toggle: when on, lists/tree request `?include_inactive=true`; when off, active-only.
- **Restore** action on inactive nodes calls `POST /api/v1/{resource}/{id}/restore` (node only; surface parent-inactive `409`).
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
- [ ] REST CRUD works for all four levels, including soft-delete (node + descendants), restore, and `?include_inactive=true`
- [ ] React UI performs CRUD exclusively through the API (no auth yet): retire confirmation, show-inactive toggle, Restore
- [ ] At least one feature shows red → green → refactor commits on `master`
- [ ] README documents how to run API + UI locally
- [ ] Seed loads all rows with `is_active=true`

---

## A2. Exercise 2 — SHIP

### A2.1 TDD practices and commit cadence

**Cadence (required):**

1. **During BUILD:** pick one feature (e.g. “cannot create duplicate sibling names”). Commit a failing test (`red`), then the implementation (`green`), then a small cleanup (`refactor`). Leave those commits unsquashed.
2. **During SHIP:** fill the rest of the pyramid, wire `make test*`, add CI. SHIP commits are tests + automation, not a rewrite of BUILD history.
3. **During RUN:** add auth-rejection tests in the same commits that introduce Basic Auth.

| Layer | Examples | Command |
|---|---|---|
| Unit | Uniqueness helpers (incl. inactive), seed line-join, soft-delete descendant walk | `make test-unit` → `pytest apps/api/tests/unit` |
| Component | Tree/list, create/edit forms, retire confirm, show-inactive toggle, Restore | `make test-component` → `npm --prefix apps/web test` (Vitest + Testing Library) |
| Integration | API + real Postgres 16 (Compose service `postgres`); soft-delete + restore + include_inactive | `make test-integration` → `pytest apps/api/tests/integration` |
| Acceptance | Browse → create → update → retire → restore → verify via API | `make test-acceptance` |

Acceptance is **mandatory**, not optional:

```bash
npx --prefix apps/web playwright install --with-deps chromium
make test-acceptance
```

CI runs the same install before Playwright.

**Invariants (BUILD/SHIP):**

- No duplicate sibling names under the same parent (`409`), including inactive names
- `DELETE` soft-deletes the node **and all descendants** in one transaction; idempotent `204` if already inactive
- FKs are `ON DELETE RESTRICT`; no physical CASCADE wipe; hard purge out of scope
- `GET` lists/tree/paths are active-only by default; `?include_inactive=true` includes retired; `GET` by id returns inactive rows
- `POST .../restore` restores the node only; child restore with inactive parent → `409`
- Seed is idempotent, asserts 2 / 8 / 25 / 61 + two wrap names, and seeds all `is_active=true`

**Invariants (RUN commits):**

- Missing/invalid Basic Auth → `401` on `/api/v1/*` (except documented public routes)
- UI retire still calls `DELETE` (soft-delete) and refreshes after login; Restore and show-inactive remain available after auth

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
- Full CRUD UI via REST, including soft-delete (retire) + restore + show-inactive toggle
- Unit / component / integration / acceptance tests documented and green (soft-delete / restore / include_inactive covered)
- CI workflow on `master`; non-Docker appendix present
- RUN: structlog, UI password + API Basic Auth, `/health` + `/health/ready`, Prometheus + Grafana, `make smoke`
- Root README: clone → up → seed → (after RUN: login) → CRUD → tests → health
- Seed all rows `is_active=true`; uniqueness holds across inactive names; hard purge out of scope

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
| CRUD includes delete | Soft-retire published/referenced master data | **Soft-delete via `is_active` in Part A** (DELETE retires node + descendants; restore explicit; hard purge out of scope) |
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

Taxonomy workbench: tree + table + inspector + activity. WCAG 2.2 AA. Soft-retire is already Part A (`is_active`); enterprise adds release-aware retire, impact preview, and governed publish workflows on top.

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

---

# Phase 2 — OAuth2 / OIDC authentication (Basic Auth retained)

> **Status: PROPOSED — awaiting review before implementation.** This phase adds
> standards-based OAuth2 / OpenID Connect (OIDC) login **in addition to** the existing
> HTTP Basic Auth. Basic Auth is **not removed**: both mechanisms are accepted concurrently
> so existing clients, tests, and the demo `admin`/`password` flow keep working unchanged.

## P2.0 Goals and non-goals

**Goals**
- Accept **either** HTTP Basic **or** an OAuth2/OIDC **Bearer** access token on every protected
  endpoint (`/api/v1/*`, `/api/v1/health/details`). Public routes (`/health`, `/health/ready`,
  `/metrics`) stay unauthenticated.
- Add a web **"Sign in with SSO"** option using the OIDC **Authorization Code flow + PKCE**,
  alongside the existing username/password (Basic) login form.
- Support **machine-to-machine** access via the OAuth2 **Client Credentials** grant (Bearer token).
- Be **backward compatible and opt-in**: when no OIDC provider is configured, behavior is
  byte-for-byte identical to today (Basic only). No existing test changes required to keep passing.

**Non-goals (this phase)**
- Replacing Basic Auth, per-record ACLs, or the full enterprise role matrix from Part B (B5.3).
- A production BFF/session server (noted as a future hardening step in P2.8; Part B B4).
- User management/registration UI — identities live in the external IdP.

## P2.1 Design: one dependency, two schemes

Introduce a single unified auth dependency `require_auth` that replaces `require_basic_auth`
at the router-inclusion sites in `app/main.py` (`_auth = [Depends(require_auth)]`). It inspects
the `Authorization` header scheme:

| Scheme | Validation | Principal produced |
|---|---|---|
| `Basic` | Existing constant-time compare vs `DEMO_USER`/`DEMO_PASSWORD` (unchanged `auth.py` logic) | `Principal(sub=username, method="basic", scopes=[])` |
| `Bearer` | Verify JWT: RS256 signature via provider **JWKS**, plus `iss`, `aud`, `exp`/`nbf` (with small clock skew) | `Principal(sub=<sub/preferred_username>, method="oidc", scopes=<scope/roles claim>)` |
| missing / unknown | `401` with `WWW-Authenticate: Basic, Bearer` | — |

- `require_basic_auth` is **kept** (composed inside `require_auth`) so current unit/integration
  tests importing it continue to pass.
- The resolved `Principal` is attached to `request.state.user` (already logged by
  `logging_setup.py`); `method` and `sub` are added to structured logs. **Tokens are never logged.**
- Authorization stays **permissive** for the MVP: any successfully authenticated principal may
  perform any CRUD action (same as today). Optional scope enforcement is described in P2.6.

## P2.2 Backend components (new / changed)

```text
apps/api/app/
  auth.py                 # keep require_basic_auth; add Principal + require_auth (compose Basic|Bearer)
  oidc.py                 # NEW: OIDC discovery (.well-known), JWKS fetch + cache, JWT verify
  config.py               # add OIDC_* settings (all optional; unset => OIDC disabled)
  main.py                 # swap _auth to Depends(require_auth); health/details too
apps/api/requirements.txt # add: pyjwt[crypto]  (JWKS/JWT verify); httpx already present
```

- **OIDC discovery + JWKS:** on first Bearer request (or lazily cached), fetch
  `${OIDC_ISSUER}/.well-known/openid-configuration` to resolve `jwks_uri`, then cache JWKS keys
  (keyed by `kid`) with a TTL and automatic refresh on unknown `kid` (handles key rotation).
- **Library choice:** `pyjwt[crypto]` for verification (small, well understood) + `httpx` for
  discovery/JWKS. Alternative `authlib` noted if we later want full client helpers.
- **Provider-agnostic:** works with Keycloak, Auth0, Microsoft Entra ID, Google, Okta, etc.

## P2.3 Configuration (all optional — unset disables OIDC)

| Env var | Purpose | Example |
|---|---|---|
| `OIDC_ISSUER` | Issuer URL (enables OIDC when set) | `https://keycloak.local/realms/retail` |
| `OIDC_AUDIENCE` | Expected `aud` of access tokens | `retail-taxonomy-api` |
| `OIDC_JWKS_URL` | Override JWKS URL (else derived from discovery) | `${OIDC_ISSUER}/protocol/openid-connect/certs` |
| `OIDC_REQUIRED_SCOPE` | Optional scope required for write ops (P2.6) | `taxonomy.write` |
| `OIDC_CLOCK_SKEW_S` | Allowed clock skew for `exp`/`nbf` | `30` |

Frontend (`apps/web`, Vite `import.meta.env`):

| Env var | Purpose |
|---|---|
| `VITE_OIDC_AUTHORITY` | IdP authority/issuer for the SPA |
| `VITE_OIDC_CLIENT_ID` | Public SPA client id |
| `VITE_OIDC_SCOPE` | e.g. `openid profile email taxonomy.read taxonomy.write` |
| `VITE_OIDC_REDIRECT_URI` | e.g. `http://localhost:5173/callback` |

`.env.example` gains commented OIDC placeholders; leaving them blank keeps Basic-only behavior.

## P2.4 Frontend changes (`apps/web`)

- Keep the current Basic-auth login card exactly as is.
- Add a **"Sign in with SSO"** button that starts Authorization Code + PKCE via
  **`oidc-client-ts`** (dependency to add). Add a `/callback` route to complete the exchange.
- `api/client.ts` gains an auth strategy: **prefer a valid OIDC access token (Bearer)** when an
  SSO session exists; otherwise fall back to stored Basic credentials. Only one `Authorization`
  header is sent per request.
- Token handling: access token in memory (with silent renew); on 401, clear session → login.
  Logout clears local state and optionally hits the IdP end-session endpoint.
- The "SSO" button only renders when `VITE_OIDC_AUTHORITY` is configured (progressive enhancement).

## P2.5 Local IdP for dev/test (Keycloak via Compose profile)

- Add an **optional** `keycloak` service to `docker-compose.yml` behind a Compose **profile**
  (`docker compose --profile oidc up`) with an imported realm (`deploy/keycloak/realm.json`)
  pre-provisioning: a SPA public client (PKCE), an API audience, an M2M confidential client,
  and `taxonomy.read` / `taxonomy.write` scopes plus a demo SSO user.
- Non-OIDC `docker compose up` is unchanged (Keycloak not started), so the default dev loop and
  the assessment path stay lightweight.

## P2.6 Optional scope-based authorization (behind a flag)

- When `OIDC_REQUIRED_SCOPE` is set, mutating verbs (`POST`/`PUT`/`DELETE`) require that scope in
  the Bearer token; reads require authentication only. Basic-auth principals are treated as
  fully authorized (unchanged demo behavior).
- Default (unset) = today's permissive behavior. This is the bridge toward Part B roles
  (Viewer/Editor/Approver…) without changing MVP semantics now.

## P2.7 Testing strategy (TDD, keep the pyramid green)

**Unit (`tests/unit/test_auth_oidc.py`)** — sign tokens locally with a test RSA keypair; stub JWKS:
- valid Bearer → principal with expected `sub`/scopes; `method="oidc"`.
- expired / `nbf` in future / wrong `aud` / wrong `iss` / bad signature / unknown `kid` → `401`.
- scheme selection: Basic path unchanged; Bearer path chosen when present.
- JWKS cache: refresh on unknown `kid`; no network call when cached.

**Integration (`tests/integration/test_auth.py` — extend, don't rewrite)**:
- **Regression:** existing Basic-auth cases still pass verbatim (proves coexistence).
- Bearer with a locally-signed token (app configured against a stubbed issuer/JWKS) → `200` on
  CRUD; tampered/expired → `401`.
- Missing creds → `401` and `WWW-Authenticate: Basic, Bearer`.
- With `OIDC_REQUIRED_SCOPE` set: read token can `GET` but not `POST` (`403`); write token can.

**Component (`apps/web`)**: render both login options; client sends Bearer when an SSO session is
mocked, Basic otherwise.

**Acceptance (Playwright)**: existing Basic-auth browse→CRUD spec stays as-is. Add an SSO happy-path
spec gated on the `oidc` Compose profile / CI service; skipped when no IdP is configured so the
default suite never flakes.

**Load test:** `perf/locustfile.py` gains an optional Bearer mode (`AUTH_MODE=bearer` with a
pre-fetched token) while Basic remains the default, so benchmarks cover both.

## P2.8 Security considerations

- Standard OIDC validation: `iss`, `aud`, `exp`/`nbf` (± skew), RS256 signature via JWKS,
  key rotation via `kid` refresh. Reject `alg=none` and symmetric algs.
- SPA token storage: access token in memory + silent renew; avoid persisting refresh tokens in
  `localStorage` (XSS risk). A server-side **BFF/session** (Part B B4) is the recommended future
  hardening and is called out as out-of-scope here.
- Never log tokens or `Authorization` headers (structlog already redacts; add explicit guard).
- CORS/redirect-URI allowlists configured per environment; PKCE + `state` + `nonce` enforced.
- Keep Basic Auth demo-only and documented as such; it is not a production credential model.

## P2.9 Milestones (TDD, incremental, each commit keeps suite green)

| # | Milestone | Deliverable |
|---|---|---|
| P2-M1 | `Principal` + `require_auth` (Basic still works) | RED: 401 `WWW-Authenticate: Basic, Bearer`; GREEN: compose Basic; regression suite green |
| P2-M2 | `oidc.py` verify + JWKS cache (unit-tested w/ local keypair) | Bearer accepted/rejected correctly; no live IdP needed for tests |
| P2-M3 | Wire `require_auth` into routers + `health/details`; config flags | Integration: Basic + Bearer both `200`; misuse `401` |
| P2-M4 | Frontend SSO (PKCE) + client auth strategy + `/callback` | Component tests; manual SSO login |
| P2-M5 | Optional scope enforcement behind `OIDC_REQUIRED_SCOPE` | Read/write scope integration tests |
| P2-M6 | Keycloak Compose profile + realm import + docs | `--profile oidc` SSO acceptance test |
| P2-M7 | Docs (README auth section), `.env.example`, perf Bearer mode | Updated README + green CI |

**Commit cadence:** one red→green→refactor sequence per milestone; Basic-auth regression tests run
on every commit to guarantee coexistence.

## P2.10 Rollout / backward compatibility

- Ship dark: with OIDC env unset, the app behaves exactly as today (Basic only) — safe to merge
  before an IdP exists.
- Enable per environment by setting `OIDC_*` (backend) and `VITE_OIDC_*` (frontend).
- No database schema changes. No breaking API changes. Demo `admin`/`password` remains valid.

## P2.11 Risks & mitigations

| Risk | Mitigation |
|---|---|
| IdP unavailable in CI | SSO acceptance gated on `oidc` profile; core suite uses local-keypair token stubs |
| Token `aud`/`iss` misconfig | Explicit config + clear `401` detail (no secrets) + startup log of expected `iss`/`aud` |
| JWKS key rotation | Cache by `kid`, refresh on miss, TTL |
| SPA XSS token theft | In-memory access token, silent renew, BFF noted as future hardening |
| Scope creep into Part B RBAC | Keep MVP permissive; scope enforcement optional + flagged |

## P2.12 Dependencies to add (on approval)

- Backend: `pyjwt[crypto]` (JWT/JWKS verification). `httpx` already present.
- Frontend: `oidc-client-ts` (Authorization Code + PKCE).
- Dev only: Keycloak image via optional Compose profile.

> **Please review this Phase 2 plan.** On approval I will implement it milestone-by-milestone
> (P2-M1 → P2-M7), keeping Basic Auth and all current tests green throughout.
