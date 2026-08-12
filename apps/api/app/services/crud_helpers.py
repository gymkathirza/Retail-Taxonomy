"""Shared CRUD helpers for hierarchy routers."""

from __future__ import annotations

import uuid
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.services.uniqueness import SiblingName, has_duplicate_sibling_name, normalize_sibling_name

T = TypeVar("T")


def get_or_404(db: Session, model: type[T], entity_id: uuid.UUID, label: str) -> T:
    obj = db.get(model, entity_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj


def raise_duplicate(detail: str) -> None:
    raise HTTPException(status_code=409, detail=detail)


def commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def check_sibling_unique(
    db: Session,
    model,
    *,
    parent_field: str | None,
    parent_id: uuid.UUID | None,
    name: str,
    exclude_id: uuid.UUID | None,
    detail: str,
) -> str:
    normalized = normalize_sibling_name(name)
    stmt = select(model)
    if parent_field is None:
        rows = list(db.scalars(stmt))
        existing = [
            SiblingName(parent_id=None, name=r.name, is_active=r.is_active, id=str(r.id)) for r in rows
        ]
        parent_key = None
    else:
        rows = list(db.scalars(stmt.where(getattr(model, parent_field) == parent_id)))
        existing = [
            SiblingName(
                parent_id=str(getattr(r, parent_field)),
                name=r.name,
                is_active=r.is_active,
                id=str(r.id),
            )
            for r in rows
        ]
        parent_key = str(parent_id) if parent_id is not None else None

    if has_duplicate_sibling_name(
        existing,
        parent_id=parent_key,
        name=normalized,
        exclude_id=str(exclude_id) if exclude_id else None,
    ):
        raise_duplicate(detail)
    return normalized
