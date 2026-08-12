"""Load / performance test suite for the Retail Taxonomy API.

Run headless (see perf/run_perf.sh or `make perf`), or interactively:

    locust -f perf/locustfile.py --host http://localhost:8000

Scenarios:
- ReadUser  : read-heavy traffic — health, collection lists, tree, paths,
              and full parent->child drill-downs (the common UI workload).
- WriteUser : mixed create/update/retire lifecycle (a smaller share of load).
"""
import random
import uuid

from locust import HttpUser, between, task


def _items(resp):
    try:
        return resp.json().get("items", [])
    except Exception:
        return []


class ReadUser(HttpUser):
    """Simulates operators browsing the taxonomy (read-heavy)."""

    weight = 4
    wait_time = between(0.1, 0.5)

    @task(1)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(1)
    def ready(self):
        self.client.get("/health/ready", name="GET /health/ready")

    @task(3)
    def list_zones(self):
        self.client.get("/api/v1/zones", name="GET /zones")

    @task(2)
    def tree(self):
        self.client.get("/api/v1/taxonomy/tree", name="GET /taxonomy/tree")

    @task(2)
    def paths(self):
        self.client.get("/api/v1/taxonomy/paths", name="GET /taxonomy/paths")

    @task(4)
    def drilldown(self):
        zones = _items(self.client.get("/api/v1/zones", name="GET /zones"))
        if not zones:
            return
        zone = random.choice(zones)
        depts = _items(
            self.client.get(
                f"/api/v1/zones/{zone['id']}/departments", name="GET /zones/:id/departments"
            )
        )
        if not depts:
            return
        dept = random.choice(depts)
        cats = _items(
            self.client.get(
                f"/api/v1/departments/{dept['id']}/categories",
                name="GET /departments/:id/categories",
            )
        )
        if not cats:
            return
        cat = random.choice(cats)
        self.client.get(
            f"/api/v1/categories/{cat['id']}/subcategories",
            name="GET /categories/:id/subcategories",
        )


class WriteUser(HttpUser):
    """Simulates stewards editing the taxonomy (create -> update -> retire)."""

    weight = 1
    wait_time = between(0.3, 1.0)

    @task
    def crud_cycle(self):
        name = f"perf-{uuid.uuid4().hex[:12]}"
        with self.client.post(
            "/api/v1/zones",
            json={"name": name, "description": "perf load test"},
            name="POST /zones",
            catch_response=True,
        ) as resp:
            if resp.status_code != 201:
                resp.failure(f"create failed: {resp.status_code}")
                return
            zone_id = resp.json()["id"]

        self.client.put(
            f"/api/v1/zones/{zone_id}",
            json={"name": name, "description": "updated"},
            name="PUT /zones/:id",
        )
        self.client.delete(f"/api/v1/zones/{zone_id}", name="DELETE /zones/:id")
