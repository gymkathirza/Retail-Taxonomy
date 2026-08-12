from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Department, Zone
from app.schemas import DepartmentCreate, DepartmentRead, DepartmentUpdate, ItemList
from app.services.crud_helpers import check_sibling_unique, commit_or_conflict, get_or_404
from app.services.db_soft_delete import restore_department, soft_delete_department

nested = APIRouter(prefix="/api/v1/zones", tags=["departments"])
router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


@nested.get("/{zone_id}/departments", response_model=ItemList)
def list_departments(
    zone_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    get_or_404(db, Zone, zone_id, "Zone")
    stmt = select(Department).where(Department.zone_id == zone_id).order_by(Department.name)
    if not include_inactive:
        stmt = stmt.where(Department.is_active.is_(True))
    return {"items": list(db.scalars(stmt))}


@nested.post("/{zone_id}/departments", response_model=DepartmentRead, status_code=201)
def create_department(
    zone_id: uuid.UUID,
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
) -> Department:
    get_or_404(db, Zone, zone_id, "Zone")
    name = check_sibling_unique(
        db,
        Department,
        parent_field="zone_id",
        parent_id=zone_id,
        name=payload.name,
        exclude_id=None,
        detail=f"A department named '{payload.name.strip()}' already exists under this zone.",
    )
    dept = Department(
        zone_id=zone_id, name=name, description=payload.description, is_active=True
    )
    db.add(dept)
    commit_or_conflict(
        db, f"A department named '{name}' already exists under this zone."
    )
    db.refresh(dept)
    return dept


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(department_id: uuid.UUID, db: Session = Depends(get_db)) -> Department:
    return get_or_404(db, Department, department_id, "Department")


@router.put("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
) -> Department:
    dept = get_or_404(db, Department, department_id, "Department")
    name = check_sibling_unique(
        db,
        Department,
        parent_field="zone_id",
        parent_id=dept.zone_id,
        name=payload.name,
        exclude_id=department_id,
        detail=f"A department named '{payload.name.strip()}' already exists under this zone.",
    )
    dept.name = name
    dept.description = payload.description
    db.add(dept)
    commit_or_conflict(
        db, f"A department named '{name}' already exists under this zone."
    )
    db.refresh(dept)
    return dept


@router.delete("/{department_id}", status_code=204, response_class=Response)
def delete_department(department_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    try:
        soft_delete_department(db, department_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Department not found") from exc
    db.commit()
    return Response(status_code=204)


@router.post("/{department_id}/restore", response_model=DepartmentRead)
def restore_department_endpoint(
    department_id: uuid.UUID, db: Session = Depends(get_db)
) -> Department:
    try:
        dept = restore_department(db, department_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Department not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(dept)
    return dept
