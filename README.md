# Retail Taxonomy Operations Platform

Public assessment package for the Full Stack coding demo (React + TypeScript + FastAPI + PostgreSQL 16).

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
| Keycloak | http://localhost:8080 (admin / admin) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin / admin unless overridden) |

**Demo login:** Basic Auth `admin` / `password`, or Keycloak SSO `sso.user` / `password` (see Authentication).

## Authentication — Basic + OAuth2/OIDC (default)

`/api/v1/*` (and `/api/v1/health/details`) accept **either**:
- **HTTP Basic Auth** — demo `admin` / `password` (always available), or
- an **OAuth2/OIDC Bearer** access token from Keycloak (and social IdPs brokered by Keycloak).

`/health`, `/health/ready`, and `/metrics` stay public. Missing/invalid credentials
return `401` with `WWW-Authenticate: Basic, Bearer`.

The default Compose stack starts **Keycloak** on `:8080` and wires API + SPA OIDC env
vars (see `.env.example`). The login page offers:

| Option | Works out of the box? | Notes |
|---|---|---|
| **Basic Auth** | Yes | `admin` / `password` |
| **Keycloak (SSO)** | Yes | Local realm user `sso.user` / `password` |
| **Google** | Demo notice until configured | Button shows “Auth required — demo only”; enable via Keycloak IdP below |
| **GitHub** | Demo notice until configured | Same as Google — no fake login bypass |

Bearer tokens are verified against Keycloak JWKS (issuer, audience, expiry, RS256).
Optional `OIDC_REQUIRED_SCOPE` gates writes (`POST/PUT/DELETE`) for OIDC principals;
Basic principals stay fully authorized.

**Quick SSO check (Keycloak local user):**

```bash
make up    # includes Keycloak; wait ~30–60s for first boot
open http://localhost:5173
# → Sign in with Keycloak (SSO) → sso.user / password
# Keycloak admin console: http://localhost:8080 (admin / admin)
# Master realm SSL is relaxed for local HTTP (see deploy/keycloak/entrypoint.sh).
```

### Enable Google / GitHub (OAuth app setup)

Until credentials are configured, **Sign in with Google / GitHub** show an in-app demo
notice (“Auth required — this is demo only”) and do **not** log you in. After setup,
enable the IdPs in Keycloak and switch the SPA buttons to real `kc_idp_hint` redirects
(or use Keycloak’s own IdP buttons on the SSO login page).

Realm stubs ship with IdPs **disabled** and `REPLACE_ME_*` placeholders.

#### 1. Google Cloud OAuth client

1. Open [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials).
2. Create **OAuth client ID** → application type **Web application**.
3. Authorized redirect URI (Keycloak broker callback):
   `http://localhost:8080/realms/retail/broker/google/endpoint`
4. Copy **Client ID** and **Client secret**.

#### 2. GitHub OAuth App

1. Open [GitHub → Settings → Developer settings → OAuth Apps → New OAuth App](https://github.com/settings/developers).
2. **Homepage URL:** `http://localhost:5173`
3. **Authorization callback URL:**
   `http://localhost:8080/realms/retail/broker/github/endpoint`
4. Register the app, then generate a **Client secret**. Copy **Client ID** and secret.

#### 3. Paste credentials into Keycloak

1. Open http://localhost:8080 → sign in as `admin` / `admin`.
2. Realm selector (top left) → **retail**.
3. **Identity providers** → **Google** → set Client ID / Client secret → Save.
4. Repeat for **GitHub**.
5. On http://localhost:5173 use **Sign in with Google** or **Sign in with GitHub**.

(Optional) You can also edit the placeholders in `deploy/keycloak/realm-retail.json` and
recreate the Keycloak container so import picks up new values (`docker compose up -d --force-recreate keycloak`).
Keycloak only re-imports a realm when it does not already exist in its DB — wipe the
Keycloak container (no persistent volume in this repo) or update via the admin UI.

#### 4. How the SPA routes social login

Buttons call OIDC Authorization Code + PKCE against Keycloak and pass `kc_idp_hint=google`
or `kc_idp_hint=github`, so Keycloak forwards straight to that provider. Tokens returned to
the SPA are still **Keycloak-issued**; the API keeps a single JWKS trust path.

Machine-to-machine (Client Credentials) example:

```bash
TOKEN=$(curl -s -d grant_type=client_credentials -d client_id=retail-taxonomy-m2m \
  -d client_secret=m2m-dev-secret \
  http://localhost:8080/realms/retail/protocol/openid-connect/token | jq -r .access_token)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/zones
```

Load-test the OIDC path: `AUTH_MODE=bearer BEARER_TOKEN=$TOKEN bash perf/run_perf.sh`.

To disable OIDC (Basic-only), clear `OIDC_ISSUER` / `VITE_OIDC_AUTHORITY` in `.env` and
omit or stop the `keycloak` service.
## Monitoring & observability

The API exposes Prometheus metrics at `GET /metrics` (unauthenticated). A `MetricsMiddleware`
records `http_requests_total{method,path,status}` and `http_request_duration_seconds{method,path}`
for every request (the `/api/v1/*` label is collapsed to keep cardinality low). structlog also
emits a structured log per request/CRUD op (`request.state.user` included, secrets/tokens never logged).

**Prometheus** (`http://localhost:9090`) scrapes `api:8000/metrics` every 15s.
- Confirm the scrape target is healthy: **Status → Targets** should show `retail-taxonomy-api` as `UP`.
  If it's `DOWN`, the `api` container isn't reachable yet (wait for its healthcheck) — metrics only
  appear once the API is up and has served at least one request.
- Try these queries in the Prometheus **Graph** tab (metrics only appear after some traffic — hit
  the UI or `curl` the API first):
  - `http_requests_total` — raw request counters
  - `sum by (status) (http_requests_total)` — requests grouped by status code
  - `rate(http_request_duration_seconds_count[1m])` — request rate
  - `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))` — p95 latency

**Grafana** (`http://localhost:3000`):
- **Login: `admin` / `admin`.** There is intentionally no sign‑up (`GF_USERS_ALLOW_SIGN_UP=false`);
  Grafana challenges with username/password because it's an admin account, not an app account.
- **For clients / read‑only viewers:** anonymous viewing is enabled
  (`GF_AUTH_ANONYMOUS_ENABLED=true`, role `Viewer`), so anyone can open Grafana and view the
  provisioned dashboard **without logging in** — the login prompt is only needed to *edit*. Override the
  admin password via `GF_SECURITY_ADMIN_PASSWORD` for non-demo use.
- A Prometheus datasource and a starter dashboard are auto‑provisioned from `docs/grafana/`.

Quick self-check that metrics are recording (no Prometheus needed):

```bash
curl -s http://localhost:8000/metrics | grep http_requests_total   # counters increase as you use the app
```

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
| `make perf` | Locust load test (override `HOST/USERS/RATE/TIME`) |

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

## Performance & load testing

A [Locust](https://locust.io/) load-test suite lives in [`perf/`](perf/). It drives the
common read workload (health, collection lists, `taxonomy/tree`, `taxonomy/paths`, and full
Zone→Department→Category→SubCategory drill-downs) plus a smaller share of write traffic
(create → update → soft-delete lifecycle). `/api/v1/*` is protected by Basic Auth, so the
suite authenticates with the demo credentials (`DEMO_USER`/`DEMO_PASSWORD`, default
`admin`/`password`).

Run it (API must be up and seeded):

```bash
make perf                              # 50 users, 30s, against http://localhost:8000
# or customize:
HOST=http://localhost:8000 USERS=100 RATE=20 TIME=60s bash perf/run_perf.sh
# interactive web UI:
locust -f perf/locustfile.py --host http://localhost:8000   # then open http://localhost:8089
```

Results (CSV + summary) are written to `perf/results/`.

### Benchmark

Recorded on the local dev environment (single `uvicorn` worker with structlog + Prometheus
middleware, PostgreSQL 16 on the same 4‑vCPU host), read‑heavy mixed workload with Basic Auth,
**50 concurrent users, 30s, spawn rate 10/s**.

| Metric | Value |
| --- | --- |
| Total requests | 6,840 |
| Failures | 0 (0.00%) |
| Throughput | ~229 req/s |
| Latency p50 | 19 ms |
| Latency p90 | 57 ms |
| Latency p95 | 71 ms |
| Latency p99 | 100 ms |
| Max | 154 ms |

Per-endpoint (median / p95 / p99, ms):

| Endpoint | req/s | p50 | p95 | p99 |
| --- | ---: | ---: | ---: | ---: |
| `GET /zones` | 59.0 | 18 | 66 | 100 |
| `GET /zones/:id/departments` | 33.0 | 20 | 61 | 88 |
| `GET /departments/:id/categories` | 24.2 | 14 | 56 | 81 |
| `GET /categories/:id/subcategories` | 24.1 | 14 | 54 | 74 |
| `GET /taxonomy/tree` | 17.0 | 30 | 96 | 110 |
| `GET /taxonomy/paths` | 16.1 | 24 | 80 | 110 |
| `GET /health` | 8.5 | 6 | 25 | 43 |
| `GET /health/ready` | 8.7 | 15 | 56 | 86 |
| `POST /zones` | 12.7 | 34 | 100 | 140 |
| `PUT /zones/:id` | 12.7 | 34 | 87 | 130 |
| `DELETE /zones/:id` | 12.7 | 18 | 60 | 72 |

**Observations:** all endpoints held a **0% error rate** at 50 concurrent users. Reads stay at
or under ~110 ms at p99; the heaviest operations are the writes (`POST`/`PUT`, p99 ~130–140 ms)
because each performs a uniqueness check plus commit. If write throughput becomes a hot path,
batch inserts or relaxing per-request logging would be the first optimizations.

## Cloud Agent environment

`.cursor/environment.json` provisions this repo for Cursor Cloud Agents **without Docker**:

- `scripts/cloud/install.sh` (install phase): installs PostgreSQL 16 + Python/Node deps and
  the API's `requirements.txt`, and installs web dependencies.
- `scripts/cloud/start.sh` (start phase): starts PostgreSQL, ensures the role/database,
  applies Alembic migrations, and seeds — idempotent across restarts.
- Named terminals run the `api` (`uvicorn`) and `web` (`vite`) dev servers.

## Assessment docs

- Plan: `Plan version 1/Retail-Taxonomy-Assessment-Aligned-Proposal.md`
- TDD milestones: `Plan version 1/Implementation-Plan-TDD-Milestones.md`
- Notes: `docs/assessment-notes.md`
