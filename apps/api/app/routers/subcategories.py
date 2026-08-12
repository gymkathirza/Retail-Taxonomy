import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db
from ..models import Subcategory
from ..schemas import NodeCreate, NodeUpdate, SubcategoryOut

router = APIRouter(tags=["subcategories"])


@router.get("/api/v1/categories/{category_id}/subcategories", response_model=dict)
def list_subcategories(category_id: uuid.UUID, include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    items = crud.list_children(db, Subcategory, "category_id", category_id, include_inactive)
    return {"items": [SubcategoryOut.model_validate(s) for s in items]}


@router.post("/api/v1/categories/{category_id}/subcategories", response_model=SubcategoryOut, status_code=201)
def create_subcategory(category_id: uuid.UUID, payload: NodeCreate, db: Session = Depends(get_db)):
    return crud.create(db, Subcategory, "category_id", category_id, payload)


@router.get("/api/v1/subcategories/{subcategory_id}", response_model=SubcategoryOut)
def get_subcategory(subcategory_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.get_one(db, Subcategory, subcategory_id)


@router.put("/api/v1/subcategories/{subcategory_id}", response_model=SubcategoryOut)
def update_subcategory(subcategory_id: uuid.UUID, payload: NodeUpdate, db: Session = Depends(get_db)):
    return crud.update(db, Subcategory, subcategory_id, payload)


@router.delete("/api/v1/subcategories/{subcategory_id}", status_code=204)
def delete_subcategory(subcategory_id: uuid.UUID, db: Session = Depends(get_db)):
    crud.soft_delete(db, Subcategory, subcategory_id)
    return Response(status_code=204)


@router.post("/api/v1/subcategories/{subcategory_id}/restore", response_model=SubcategoryOut)
def restore_subcategory(subcategory_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.restore(db, Subcategory, subcategory_id)
