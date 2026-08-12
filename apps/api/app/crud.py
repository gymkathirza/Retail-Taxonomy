"""Service layer for the four-level taxonomy with soft-delete + restore."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Category, Department, Subcategory, Zone
from .problems import ProblemException

DUP_TYPE = "https://example.com/problems/duplicate-name"

# Ordered parent -> child chain used for cascading soft-delete.
CHILD_OF = {Zone: Department, Department: Category, Category: Subcategory, Subcategory: None}
PARENT_FK = {Department: "zone_id", Category: "department_id", Subcategory: "category_id"}
PARENT_MODEL_BY_FK = {"zone_id": Zone, "department_id": Department, "category_id": Category}
LABEL = {Zone: "zone", Department: "department", Category: "category", Subcategory: "subcategory"}


def _get(db: Session, model, obj_id: uuid.UUID):
    obj = db.get(model, obj_id)
    if obj is None:
        raise ProblemException(404, "Not Found", f"No {LABEL[model]} with id {obj_id}.")
    return obj


def _duplicate_check(db: Session, model, name: str, parent_field: str | None, parent_id, exclude_id=None):
    stmt = select(model).where(model.name == name)
    if parent_field is not None:
        stmt = stmt.where(getattr(model, parent_field) == parent_id)
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ProblemException(
            409,
            "Conflict",
            f"A {LABEL[model]} named '{name}' already exists under this parent.",
            DUP_TYPE,
        )


def list_children(db: Session, model, parent_field: str | None, parent_id, include_inactive: bool):
    stmt = select(model)
    if parent_field is not None:
        stmt = stmt.where(getattr(model, parent_field) == parent_id)
    if not include_inactive:
        stmt = stmt.where(model.is_active.is_(True))
    stmt = stmt.order_by(model.name)
    return list(db.scalars(stmt).all())


def get_one(db: Session, model, obj_id: uuid.UUID):
    return _get(db, model, obj_id)


def create(db: Session, model, parent_field: str | None, parent_id, data):
    if parent_field is not None:
        _get(db, PARENT_MODEL_BY_FK[parent_field], parent_id)
    _duplicate_check(db, model, data.name, parent_field, parent_id)
    kwargs = {"name": data.name, "description": data.description}
    if parent_field is not None:
        kwargs[parent_field] = parent_id
    obj = model(**kwargs)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, model, obj_id: uuid.UUID, data):
    obj = _get(db, model, obj_id)
    parent_field = PARENT_FK.get(model)
    parent_id = getattr(obj, parent_field) if parent_field else None
    _duplicate_check(db, model, data.name, parent_field, parent_id, exclude_id=obj_id)
    obj.name = data.name
    obj.description = data.description
    db.commit()
    db.refresh(obj)
    return obj


def _cascade_deactivate(db: Session, model, obj):
    obj.is_active = False
    child = CHILD_OF[model]
    if child is None:
        return
    fk = PARENT_FK[child]
    children = db.scalars(select(child).where(getattr(child, fk) == obj.id)).all()
    for c in children:
        _cascade_deactivate(db, child, c)


def soft_delete(db: Session, model, obj_id: uuid.UUID):
    obj = _get(db, model, obj_id)
    _cascade_deactivate(db, model, obj)
    db.commit()


def restore(db: Session, model, obj_id: uuid.UUID):
    obj = _get(db, model, obj_id)
    parent_field = PARENT_FK.get(model)
    if parent_field is not None:
        parent_model = PARENT_MODEL_BY_FK[parent_field]
        parent = db.get(parent_model, getattr(obj, parent_field))
        if parent is not None and not parent.is_active:
            raise ProblemException(
                409,
                "Conflict",
                f"Cannot restore {LABEL[model]} while its parent is inactive.",
                DUP_TYPE,
            )
    obj.is_active = True
    db.commit()
    db.refresh(obj)
    return obj
