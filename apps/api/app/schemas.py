import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NodeBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class NodeCreate(NodeBase):
    pass


class NodeUpdate(NodeBase):
    pass


class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DepartmentOut(ZoneOut):
    zone_id: uuid.UUID


class CategoryOut(ZoneOut):
    department_id: uuid.UUID


class SubcategoryOut(ZoneOut):
    category_id: uuid.UUID


class Collection(BaseModel):
    items: list


class PathOut(BaseModel):
    subcategory_id: uuid.UUID
    zone: str
    department: str
    category: str
    subcategory: str
    full_path: str
    is_active: bool
