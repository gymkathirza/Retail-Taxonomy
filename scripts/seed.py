#!/usr/bin/env python3
"""Idempotent seed loader for the retail taxonomy.

Reads the canonical unwrapped CSV (``data/seed/taxonomy.csv``) and upserts the
four-level hierarchy (zones -> departments -> categories -> subcategories).
The CSV keeps the PDF column name ``Location``; it is mapped into ``zones``.

Running this script repeatedly is safe: existing nodes are matched by
(parent, name) and left untouched.
"""
import csv
import os
import sys
import uuid
from pathlib import Path

# Allow running as `python scripts/seed.py` from the repo root or /app.
_API_DIR = Path(__file__).resolve().parents[1] / "apps" / "api"
for candidate in (_API_DIR, Path("/app")):
    if (candidate / "app").is_dir():
        sys.path.insert(0, str(candidate))
        break

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Category, Department, Subcategory, Zone  # noqa: E402


def _csv_path() -> Path:
    env = os.environ.get("SEED_CSV")
    if env:
        return Path(env)
    for candidate in (
        Path(__file__).resolve().parents[1] / "data" / "seed" / "taxonomy.csv",
        Path("/app/data/seed/taxonomy.csv"),
        Path("data/seed/taxonomy.csv"),
    ):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not locate data/seed/taxonomy.csv (set SEED_CSV).")


def _get_or_create(db: Session, model, name: str, parent_field: str | None, parent_id):
    stmt = select(model).where(model.name == name)
    if parent_field is not None:
        stmt = stmt.where(getattr(model, parent_field) == parent_id)
    obj = db.scalar(stmt)
    if obj is not None:
        return obj, False
    kwargs = {"id": uuid.uuid4(), "name": name, "is_active": True}
    if parent_field is not None:
        kwargs[parent_field] = parent_id
    obj = model(**kwargs)
    db.add(obj)
    db.flush()
    return obj, True


def seed() -> dict:
    path = _csv_path()
    created = {"zones": 0, "departments": 0, "categories": 0, "subcategories": 0}
    db = SessionLocal()
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                zone_name = (row.get("Location") or row.get("Zone") or "").strip()
                dept_name = (row.get("Department") or "").strip()
                cat_name = (row.get("Category") or "").strip()
                sub_name = (row.get("SubCategory") or row.get("Subcategory") or "").strip()
                if not (zone_name and dept_name and cat_name and sub_name):
                    continue

                zone, c = _get_or_create(db, Zone, zone_name, None, None)
                created["zones"] += c
                dept, c = _get_or_create(db, Department, dept_name, "zone_id", zone.id)
                created["departments"] += c
                cat, c = _get_or_create(db, Category, cat_name, "department_id", dept.id)
                created["categories"] += c
                _sub, c = _get_or_create(db, Subcategory, sub_name, "category_id", cat.id)
                created["subcategories"] += c
        db.commit()
    finally:
        db.close()
    return created


def main() -> None:
    from sqlalchemy import func

    created = seed()
    db = SessionLocal()
    try:
        totals = {
            "zones": db.scalar(select(func.count()).select_from(Zone)),
            "departments": db.scalar(select(func.count()).select_from(Department)),
            "categories": db.scalar(select(func.count()).select_from(Category)),
            "subcategories": db.scalar(select(func.count()).select_from(Subcategory)),
        }
    finally:
        db.close()
    print(f"Seed complete. Created this run: {created}")
    print(f"Totals now: {totals}")


if __name__ == "__main__":
    main()
