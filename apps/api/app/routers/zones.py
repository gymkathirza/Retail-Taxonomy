import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db
from ..models import Zone
from ..schemas import NodeCreate, NodeUpdate, ZoneOut

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


@router.get("", response_model=dict)
def list_zones(include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    items = crud.list_children(db, Zone, None, None, include_inactive)
    return {"items": [ZoneOut.model_validate(z) for z in items]}


@router.post("", response_model=ZoneOut, status_code=201)
def create_zone(payload: NodeCreate, db: Session = Depends(get_db)):
    return crud.create(db, Zone, None, None, payload)


@router.get("/{zone_id}", response_model=ZoneOut)
def get_zone(zone_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.get_one(db, Zone, zone_id)


@router.put("/{zone_id}", response_model=ZoneOut)
def update_zone(zone_id: uuid.UUID, payload: NodeUpdate, db: Session = Depends(get_db)):
    return crud.update(db, Zone, zone_id, payload)


@router.delete("/{zone_id}", status_code=204)
def delete_zone(zone_id: uuid.UUID, db: Session = Depends(get_db)):
    crud.soft_delete(db, Zone, zone_id)
    return Response(status_code=204)


@router.post("/{zone_id}/restore", response_model=ZoneOut)
def restore_zone(zone_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.restore(db, Zone, zone_id)
