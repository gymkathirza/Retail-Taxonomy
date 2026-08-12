import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db
from ..models import Category
from ..schemas import CategoryOut, NodeCreate, NodeUpdate

router = APIRouter(tags=["categories"])


@router.get("/api/v1/departments/{department_id}/categories", response_model=dict)
def list_categories(department_id: uuid.UUID, include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    items = crud.list_children(db, Category, "department_id", department_id, include_inactive)
    return {"items": [CategoryOut.model_validate(c) for c in items]}


@router.post("/api/v1/departments/{department_id}/categories", response_model=CategoryOut, status_code=201)
def create_category(department_id: uuid.UUID, payload: NodeCreate, db: Session = Depends(get_db)):
    return crud.create(db, Category, "department_id", department_id, payload)


@router.get("/api/v1/categories/{category_id}", response_model=CategoryOut)
def get_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.get_one(db, Category, category_id)


@router.put("/api/v1/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: uuid.UUID, payload: NodeUpdate, db: Session = Depends(get_db)):
    return crud.update(db, Category, category_id, payload)


@router.delete("/api/v1/categories/{category_id}", status_code=204)
def delete_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    crud.soft_delete(db, Category, category_id)
    return Response(status_code=204)


@router.post("/api/v1/categories/{category_id}/restore", response_model=CategoryOut)
def restore_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.restore(db, Category, category_id)
