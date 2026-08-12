from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, Department
from app.schemas import CategoryCreate, CategoryRead, CategoryUpdate, ItemList
from app.services.crud_helpers import check_sibling_unique, commit_or_conflict, get_or_404
from app.services.db_soft_delete import restore_category, soft_delete_category

nested = APIRouter(prefix="/api/v1/departments", tags=["categories"])
router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@nested.get("/{department_id}/categories", response_model=ItemList)
def list_categories(
    department_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    get_or_404(db, Department, department_id, "Department")
    stmt = (
        select(Category).where(Category.department_id == department_id).order_by(Category.name)
    )
    if not include_inactive:
        stmt = stmt.where(Category.is_active.is_(True))
    return {"items": list(db.scalars(stmt))}


@nested.post("/{department_id}/categories", response_model=CategoryRead, status_code=201)
def create_category(
    department_id: uuid.UUID,
    payload: CategoryCreate,
    db: Session = Depends(get_db),
) -> Category:
    get_or_404(db, Department, department_id, "Department")
    name = check_sibling_unique(
        db,
        Category,
        parent_field="department_id",
        parent_id=department_id,
        name=payload.name,
        exclude_id=None,
        detail=(
            f"A category named '{payload.name.strip()}' already exists under this department."
        ),
    )
    category = Category(
        department_id=department_id,
        name=name,
        description=payload.description,
        is_active=True,
    )
    db.add(category)
    commit_or_conflict(
        db, f"A category named '{name}' already exists under this department."
    )
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: uuid.UUID, db: Session = Depends(get_db)) -> Category:
    return get_or_404(db, Category, category_id, "Category")


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> Category:
    category = get_or_404(db, Category, category_id, "Category")
    name = check_sibling_unique(
        db,
        Category,
        parent_field="department_id",
        parent_id=category.department_id,
        name=payload.name,
        exclude_id=category_id,
        detail=(
            f"A category named '{payload.name.strip()}' already exists under this department."
        ),
    )
    category.name = name
    category.description = payload.description
    db.add(category)
    commit_or_conflict(
        db, f"A category named '{name}' already exists under this department."
    )
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204, response_class=Response)
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    try:
        soft_delete_category(db, category_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Category not found") from exc
    db.commit()
    return Response(status_code=204)


@router.post("/{category_id}/restore", response_model=CategoryRead)
def restore_category_endpoint(
    category_id: uuid.UUID, db: Session = Depends(get_db)
) -> Category:
    try:
        category = restore_category(db, category_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Category not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(category)
    return category
