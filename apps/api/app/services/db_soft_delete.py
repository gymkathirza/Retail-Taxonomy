"""Database-backed soft-delete and restore helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Category, Department, Subcategory, Zone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def soft_delete_zone(db: Session, zone_id: uuid.UUID) -> None:
    zone = db.get(Zone, zone_id)
    if zone is None:
        raise KeyError(zone_id)
    dept_ids = list(db.scalars(select(Department.id).where(Department.zone_id == zone_id)))
    cat_ids = list(
        db.scalars(select(Category.id).where(Category.department_id.in_(dept_ids))) if dept_ids else []
    )
    now = _now()
    if cat_ids:
        db.execute(
            update(Subcategory)
            .where(Subcategory.category_id.in_(cat_ids))
            .values(is_active=False, updated_at=now)
        )
        db.execute(
            update(Category).where(Category.id.in_(cat_ids)).values(is_active=False, updated_at=now)
        )
    if dept_ids:
        db.execute(
            update(Department)
            .where(Department.id.in_(dept_ids))
            .values(is_active=False, updated_at=now)
        )
    zone.is_active = False
    zone.updated_at = now
    db.add(zone)


def soft_delete_department(db: Session, department_id: uuid.UUID) -> None:
    dept = db.get(Department, department_id)
    if dept is None:
        raise KeyError(department_id)
    cat_ids = list(
        db.scalars(select(Category.id).where(Category.department_id == department_id))
    )
    now = _now()
    if cat_ids:
        db.execute(
            update(Subcategory)
            .where(Subcategory.category_id.in_(cat_ids))
            .values(is_active=False, updated_at=now)
        )
        db.execute(
            update(Category).where(Category.id.in_(cat_ids)).values(is_active=False, updated_at=now)
        )
    dept.is_active = False
    dept.updated_at = now
    db.add(dept)


def soft_delete_category(db: Session, category_id: uuid.UUID) -> None:
    category = db.get(Category, category_id)
    if category is None:
        raise KeyError(category_id)
    now = _now()
    db.execute(
        update(Subcategory)
        .where(Subcategory.category_id == category_id)
        .values(is_active=False, updated_at=now)
    )
    category.is_active = False
    category.updated_at = now
    db.add(category)


def soft_delete_subcategory(db: Session, subcategory_id: uuid.UUID) -> None:
    sub = db.get(Subcategory, subcategory_id)
    if sub is None:
        raise KeyError(subcategory_id)
    sub.is_active = False
    sub.updated_at = _now()
    db.add(sub)


def restore_zone(db: Session, zone_id: uuid.UUID) -> Zone:
    zone = db.get(Zone, zone_id)
    if zone is None:
        raise KeyError(zone_id)
    zone.is_active = True
    zone.updated_at = _now()
    db.add(zone)
    return zone


def restore_department(db: Session, department_id: uuid.UUID) -> Department:
    dept = db.get(Department, department_id)
    if dept is None:
        raise KeyError(department_id)
    zone = db.get(Zone, dept.zone_id)
    if zone is None or not zone.is_active:
        raise ValueError("Cannot restore department while its parent zone is inactive")
    dept.is_active = True
    dept.updated_at = _now()
    db.add(dept)
    return dept


def restore_category(db: Session, category_id: uuid.UUID) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise KeyError(category_id)
    dept = db.get(Department, category.department_id)
    if dept is None or not dept.is_active:
        raise ValueError("Cannot restore category while its parent department is inactive")
    category.is_active = True
    category.updated_at = _now()
    db.add(category)
    return category


def restore_subcategory(db: Session, subcategory_id: uuid.UUID) -> Subcategory:
    sub = db.get(Subcategory, subcategory_id)
    if sub is None:
        raise KeyError(subcategory_id)
    category = db.get(Category, sub.category_id)
    if category is None or not category.is_active:
        raise ValueError("Cannot restore subcategory while its parent category is inactive")
    sub.is_active = True
    sub.updated_at = _now()
    db.add(sub)
    return sub
