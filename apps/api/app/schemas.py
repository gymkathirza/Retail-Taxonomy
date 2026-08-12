"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ZoneCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class ZoneUpdate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    zone_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    department_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SubcategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class SubcategoryUpdate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class SubcategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ItemList(BaseModel):
    items: list[ZoneRead | DepartmentRead | CategoryRead | SubcategoryRead]


class TaxonomyPath(BaseModel):
    subcategory_id: UUID
    zone: str
    department: str
    category: str
    subcategory: str
    full_path: str
    is_active: bool


class TaxonomyTreeSubcategory(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool


class TaxonomyTreeCategory(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    subcategories: list[TaxonomyTreeSubcategory]


class TaxonomyTreeDepartment(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    categories: list[TaxonomyTreeCategory]


class TaxonomyTreeZone(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
    departments: list[TaxonomyTreeDepartment]


class TaxonomyTreeResponse(BaseModel):
    items: list[TaxonomyTreeZone]


class TaxonomyPathsResponse(BaseModel):
    items: list[TaxonomyPath]
