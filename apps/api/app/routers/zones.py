from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Zone
from app.schemas import ItemList, ZoneCreate, ZoneRead, ZoneUpdate
from app.services.crud_helpers import check_sibling_unique, commit_or_conflict, get_or_404
from app.services.db_soft_delete import restore_zone, soft_delete_zone

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


@router.get("", response_model=ItemList)
def list_zones(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(Zone).order_by(Zone.name)
    if not include_inactive:
        stmt = stmt.where(Zone.is_active.is_(True))
    return {"items": list(db.scalars(stmt))}


@router.post("", response_model=ZoneRead, status_code=201)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db)) -> Zone:
    name = check_sibling_unique(
        db,
        Zone,
        parent_field=None,
        parent_id=None,
        name=payload.name,
        exclude_id=None,
        detail=f"A zone named '{payload.name.strip()}' already exists.",
    )
    zone = Zone(name=name, description=payload.description, is_active=True)
    db.add(zone)
    commit_or_conflict(db, f"A zone named '{name}' already exists.")
    db.refresh(zone)
    return zone


@router.get("/{zone_id}", response_model=ZoneRead)
def get_zone(zone_id: uuid.UUID, db: Session = Depends(get_db)) -> Zone:
    return get_or_404(db, Zone, zone_id, "Zone")


@router.put("/{zone_id}", response_model=ZoneRead)
def update_zone(zone_id: uuid.UUID, payload: ZoneUpdate, db: Session = Depends(get_db)) -> Zone:
    zone = get_or_404(db, Zone, zone_id, "Zone")
    name = check_sibling_unique(
        db,
        Zone,
        parent_field=None,
        parent_id=None,
        name=payload.name,
        exclude_id=zone_id,
        detail=f"A zone named '{payload.name.strip()}' already exists.",
    )
    zone.name = name
    zone.description = payload.description
    db.add(zone)
    commit_or_conflict(db, f"A zone named '{name}' already exists.")
    db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=204, response_class=Response)
def delete_zone(zone_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    try:
        soft_delete_zone(db, zone_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Zone not found") from exc
    db.commit()
    return Response(status_code=204)


@router.post("/{zone_id}/restore", response_model=ZoneRead)
def restore_zone_endpoint(zone_id: uuid.UUID, db: Session = Depends(get_db)) -> Zone:
    try:
        zone = restore_zone(db, zone_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Zone not found") from exc
    db.commit()
    db.refresh(zone)
    return zone
