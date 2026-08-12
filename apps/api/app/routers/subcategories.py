from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, Subcategory
from app.schemas import ItemList, SubcategoryCreate, SubcategoryRead, SubcategoryUpdate
from app.services.crud_helpers import check_sibling_unique, commit_or_conflict, get_or_404
from app.services.db_soft_delete import restore_subcategory, soft_delete_subcategory

nested = APIRouter(prefix="/api/v1/categories", tags=["subcategories"])
router = APIRouter(prefix="/api/v1/subcategories", tags=["subcategories"])


@nested.get("/{category_id}/subcategories", response_model=ItemList)
def list_subcategories(
    category_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    get_or_404(db, Category, category_id, "Category")
    stmt = (
        select(Subcategory)
        .where(Subcategory.category_id == category_id)
        .order_by(Subcategory.name)
    )
    if not include_inactive:
        stmt = stmt.where(Subcategory.is_active.is_(True))
    return {"items": list(db.scalars(stmt))}


@nested.post("/{category_id}/subcategories", response_model=SubcategoryRead, status_code=201)
def create_subcategory(
    category_id: uuid.UUID,
    payload: SubcategoryCreate,
    db: Session = Depends(get_db),
) -> Subcategory:
    get_or_404(db, Category, category_id, "Category")
    name = check_sibling_unique(
        db,
        Subcategory,
        parent_field="category_id",
        parent_id=category_id,
        name=payload.name,
        exclude_id=None,
        detail=(
            f"A subcategory named '{payload.name.strip()}' already exists under this category."
        ),
    )
    sub = Subcategory(
        category_id=category_id,
        name=name,
        description=payload.description,
        is_active=True,
    )
    db.add(sub)
    commit_or_conflict(
        db, f"A subcategory named '{name}' already exists under this category."
    )
    db.refresh(sub)
    return sub


@router.get("/{subcategory_id}", response_model=SubcategoryRead)
def get_subcategory(subcategory_id: uuid.UUID, db: Session = Depends(get_db)) -> Subcategory:
    return get_or_404(db, Subcategory, subcategory_id, "Subcategory")


@router.put("/{subcategory_id}", response_model=SubcategoryRead)
def update_subcategory(
    subcategory_id: uuid.UUID,
    payload: SubcategoryUpdate,
    db: Session = Depends(get_db),
) -> Subcategory:
    sub = get_or_404(db, Subcategory, subcategory_id, "Subcategory")
    name = check_sibling_unique(
        db,
        Subcategory,
        parent_field="category_id",
        parent_id=sub.category_id,
        name=payload.name,
        exclude_id=subcategory_id,
        detail=(
            f"A subcategory named '{payload.name.strip()}' already exists under this category."
        ),
    )
    sub.name = name
    sub.description = payload.description
    db.add(sub)
    commit_or_conflict(
        db, f"A subcategory named '{name}' already exists under this category."
    )
    db.refresh(sub)
    return sub


@router.delete("/{subcategory_id}", status_code=204, response_class=Response)
def delete_subcategory(subcategory_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    try:
        soft_delete_subcategory(db, subcategory_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Subcategory not found") from exc
    db.commit()
    return Response(status_code=204)


@router.post("/{subcategory_id}/restore", response_model=SubcategoryRead)
def restore_subcategory_endpoint(
    subcategory_id: uuid.UUID, db: Session = Depends(get_db)
) -> Subcategory:
    try:
        sub = restore_subcategory(db, subcategory_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Subcategory not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(sub)
    return sub
