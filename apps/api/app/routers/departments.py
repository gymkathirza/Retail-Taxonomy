import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db
from ..models import Department
from ..schemas import DepartmentOut, NodeCreate, NodeUpdate

router = APIRouter(tags=["departments"])


@router.get("/api/v1/zones/{zone_id}/departments", response_model=dict)
def list_departments(zone_id: uuid.UUID, include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    items = crud.list_children(db, Department, "zone_id", zone_id, include_inactive)
    return {"items": [DepartmentOut.model_validate(d) for d in items]}


@router.post("/api/v1/zones/{zone_id}/departments", response_model=DepartmentOut, status_code=201)
def create_department(zone_id: uuid.UUID, payload: NodeCreate, db: Session = Depends(get_db)):
    return crud.create(db, Department, "zone_id", zone_id, payload)


@router.get("/api/v1/departments/{department_id}", response_model=DepartmentOut)
def get_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.get_one(db, Department, department_id)


@router.put("/api/v1/departments/{department_id}", response_model=DepartmentOut)
def update_department(department_id: uuid.UUID, payload: NodeUpdate, db: Session = Depends(get_db)):
    return crud.update(db, Department, department_id, payload)


@router.delete("/api/v1/departments/{department_id}", status_code=204)
def delete_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    crud.soft_delete(db, Department, department_id)
    return Response(status_code=204)


@router.post("/api/v1/departments/{department_id}/restore", response_model=DepartmentOut)
def restore_department(department_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.restore(db, Department, department_id)
