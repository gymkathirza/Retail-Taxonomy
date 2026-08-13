from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Category, Department, Subcategory, Zone
from app.schemas import TaxonomyPath, TaxonomyPathsResponse, TaxonomyTreeResponse
from app.services.export_taxonomy import build_excel, build_word

router = APIRouter(prefix="/api/v1/taxonomy", tags=["taxonomy"])


def _path_items(db: Session, include_inactive: bool) -> list[TaxonomyPath]:
    stmt = (
        select(Subcategory, Category, Department, Zone)
        .join(Category, Category.id == Subcategory.category_id)
        .join(Department, Department.id == Category.department_id)
        .join(Zone, Zone.id == Department.zone_id)
        .order_by(Zone.name, Department.name, Category.name, Subcategory.name)
    )
    if not include_inactive:
        stmt = stmt.where(
            Subcategory.is_active.is_(True),
            Category.is_active.is_(True),
            Department.is_active.is_(True),
            Zone.is_active.is_(True),
        )
    rows = db.execute(stmt).all()
    return [
        TaxonomyPath(
            subcategory_id=sub.id,
            zone=zone.name,
            department=dept.name,
            category=cat.name,
            subcategory=sub.name,
            full_path=f"{zone.name} > {dept.name} > {cat.name} > {sub.name}",
            is_active=sub.is_active,
        )
        for sub, cat, dept, zone in rows
    ]


@router.get("/tree", response_model=TaxonomyTreeResponse)
def taxonomy_tree(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    stmt = (
        select(Zone)
        .options(
            selectinload(Zone.departments)
            .selectinload(Department.categories)
            .selectinload(Category.subcategories)
        )
        .order_by(Zone.name)
    )
    if not include_inactive:
        stmt = stmt.where(Zone.is_active.is_(True))
    zones = list(db.scalars(stmt).unique())

    items = []
    for zone in zones:
        departments = []
        for dept in sorted(zone.departments, key=lambda d: d.name):
            if not include_inactive and not dept.is_active:
                continue
            categories = []
            for cat in sorted(dept.categories, key=lambda c: c.name):
                if not include_inactive and not cat.is_active:
                    continue
                subs = [
                    {
                        "id": s.id,
                        "name": s.name,
                        "description": s.description,
                        "is_active": s.is_active,
                    }
                    for s in sorted(cat.subcategories, key=lambda x: x.name)
                    if include_inactive or s.is_active
                ]
                categories.append(
                    {
                        "id": cat.id,
                        "name": cat.name,
                        "description": cat.description,
                        "is_active": cat.is_active,
                        "subcategories": subs,
                    }
                )
            departments.append(
                {
                    "id": dept.id,
                    "name": dept.name,
                    "description": dept.description,
                    "is_active": dept.is_active,
                    "categories": categories,
                }
            )
        items.append(
            {
                "id": zone.id,
                "name": zone.name,
                "description": zone.description,
                "is_active": zone.is_active,
                "departments": departments,
            }
        )
    return {"items": items}


@router.get("/paths", response_model=TaxonomyPathsResponse)
def taxonomy_paths(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    return {"items": _path_items(db, include_inactive)}


@router.get("/export.xlsx")
def export_taxonomy_excel(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> Response:
    """Download the taxonomy hierarchy as a Microsoft Excel workbook."""
    content = build_excel(_path_items(db, include_inactive))
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="retail-taxonomy.xlsx"',
        },
    )


@router.get("/export.docx")
def export_taxonomy_word(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
) -> Response:
    """Download the taxonomy hierarchy as a Microsoft Word document."""
    content = build_word(_path_items(db, include_inactive))
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": 'attachment; filename="retail-taxonomy.docx"',
        },
    )
