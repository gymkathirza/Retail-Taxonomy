#!/usr/bin/env python3
"""Idempotent seed of taxonomy hierarchy from data/seed/taxonomy.csv."""

from __future__ import annotations

import csv
import os
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Allow `python /app/scripts/seed.py` and host `python scripts/seed.py`
API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# Inside the API container WORKDIR is /app (apps/api mounted there).
CONTAINER_API_ROOT = Path("/app")
if CONTAINER_API_ROOT.joinpath("app").is_dir() and str(CONTAINER_API_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTAINER_API_ROOT))

from app.models import Category, Department, Subcategory, Zone  # noqa: E402


def _repo_root() -> Path:
    # Host: scripts/ -> repo root. Container: /app/scripts -> prefer /data or mounted repo.
    here = Path(__file__).resolve().parent
    if (here.parent / "data" / "seed" / "taxonomy.csv").is_file():
        return here.parent
    if Path("/data/seed/taxonomy.csv").is_file():
        return Path("/")
    return here.parent


def _csv_path() -> Path:
    env_path = os.environ.get("TAXONOMY_SEED_CSV")
    if env_path:
        return Path(env_path)
    return _repo_root() / "data" / "seed" / "taxonomy.csv"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://taxonomy:taxonomy@localhost:5432/taxonomy",
    )


def _get_or_create(
    session: Session,
    model,
    *,
    filters: dict,
    defaults: dict,
):
    stmt = select(model)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    obj = session.scalars(stmt).first()
    if obj is not None:
        changed = False
        for key, value in defaults.items():
            if getattr(obj, key) != value:
                setattr(obj, key, value)
                changed = True
        if changed:
            session.add(obj)
        return obj, False
    obj = model(id=uuid.uuid4(), **filters, **defaults)
    session.add(obj)
    session.flush()
    return obj, True


def seed(session: Session, csv_path: Path) -> dict[str, int]:
    created = {"zones": 0, "departments": 0, "categories": 0, "subcategories": 0}
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            zone_name = row["Location"].strip()
            dept_name = row["Department"].strip()
            cat_name = row["Category"].strip()
            sub_name = row["SubCategory"].strip()

            zone, created_zone = _get_or_create(
                session,
                Zone,
                filters={"name": zone_name},
                defaults={"description": None, "is_active": True},
            )
            if created_zone:
                created["zones"] += 1

            dept, created_dept = _get_or_create(
                session,
                Department,
                filters={"zone_id": zone.id, "name": dept_name},
                defaults={"description": None, "is_active": True},
            )
            if created_dept:
                created["departments"] += 1

            cat, created_cat = _get_or_create(
                session,
                Category,
                filters={"department_id": dept.id, "name": cat_name},
                defaults={"description": None, "is_active": True},
            )
            if created_cat:
                created["categories"] += 1

            _, created_sub = _get_or_create(
                session,
                Subcategory,
                filters={"category_id": cat.id, "name": sub_name},
                defaults={"description": None, "is_active": True},
            )
            if created_sub:
                created["subcategories"] += 1

    session.commit()
    return created


def main() -> None:
    csv_path = _csv_path()
    if not csv_path.is_file():
        raise SystemExit(f"Seed CSV not found: {csv_path}")

    engine = create_engine(_database_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    from sqlalchemy import func

    with SessionLocal() as session:
        counts = seed(session, csv_path)
        summary = {
            "zones": session.scalar(select(func.count()).select_from(Zone)),
            "departments": session.scalar(select(func.count()).select_from(Department)),
            "categories": session.scalar(select(func.count()).select_from(Category)),
            "subcategories": session.scalar(select(func.count()).select_from(Subcategory)),
        }
    print(f"Seed complete from {csv_path}")
    print(f"Created this run: {counts}")
    print(f"Totals: {summary}")
    expected = {"zones": 2, "departments": 8, "categories": 25, "subcategories": 61}
    if summary != expected:
        raise SystemExit(f"Seed count mismatch: got {summary}, expected {expected}")


if __name__ == "__main__":
    main()
