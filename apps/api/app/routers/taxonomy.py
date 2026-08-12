from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Category, Department, Subcategory, Zone

router = APIRouter(prefix="/api/v1/taxonomy", tags=["taxonomy"])


def _active(query, model, include_inactive: bool):
    return query if include_inactive else query.where(model.is_active.is_(True))


@router.get("/tree")
def get_tree(include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    zones = db.scalars(_active(select(Zone), Zone, include_inactive).order_by(Zone.name)).all()
    tree = []
    for z in zones:
        depts = db.scalars(
            _active(select(Department).where(Department.zone_id == z.id), Department, include_inactive).order_by(Department.name)
        ).all()
        z_node = {"id": str(z.id), "name": z.name, "is_active": z.is_active, "level": "zone", "children": []}
        for d in depts:
            cats = db.scalars(
                _active(select(Category).where(Category.department_id == d.id), Category, include_inactive).order_by(Category.name)
            ).all()
            d_node = {"id": str(d.id), "name": d.name, "is_active": d.is_active, "level": "department", "children": []}
            for c in cats:
                subs = db.scalars(
                    _active(select(Subcategory).where(Subcategory.category_id == c.id), Subcategory, include_inactive).order_by(Subcategory.name)
                ).all()
                c_node = {"id": str(c.id), "name": c.name, "is_active": c.is_active, "level": "category", "children": []}
                for s in subs:
                    c_node["children"].append(
                        {"id": str(s.id), "name": s.name, "is_active": s.is_active, "level": "subcategory", "children": []}
                    )
                d_node["children"].append(c_node)
            z_node["children"].append(d_node)
        tree.append(z_node)
    return {"items": tree}


@router.get("/paths")
def get_paths(include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    stmt = (
        select(Subcategory, Category, Department, Zone)
        .join(Category, Subcategory.category_id == Category.id)
        .join(Department, Category.department_id == Department.id)
        .join(Zone, Department.zone_id == Zone.id)
    )
    if not include_inactive:
        stmt = stmt.where(
            Subcategory.is_active.is_(True),
            Category.is_active.is_(True),
            Department.is_active.is_(True),
            Zone.is_active.is_(True),
        )
    rows = db.execute(stmt.order_by(Zone.name, Department.name, Category.name, Subcategory.name)).all()
    items = [
        {
            "subcategory_id": str(s.id),
            "zone": z.name,
            "department": d.name,
            "category": c.name,
            "subcategory": s.name,
            "full_path": f"{z.name} > {d.name} > {c.name} > {s.name}",
            "is_active": s.is_active,
        }
        for s, c, d, z in rows
    ]
    return {"items": items}
