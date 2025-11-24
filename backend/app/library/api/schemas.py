from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.library.models import TemplateType, TemplateVisibility


class CategorySchema(BaseModel):
    """Category schema."""

    id: UUID
    name: str
    visibility: TemplateVisibility
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryCreateSchema(BaseModel):
    """Schema for creating a category."""

    name: str
    visibility: TemplateVisibility = TemplateVisibility.PUBLIC


class TemplateSchema(BaseModel):
    """Template schema."""

    id: UUID
    name: str
    team_id: UUID
    user_id: UUID
    category_id: UUID
    category_name: str | None = None
    type: TemplateType
    visibility: TemplateVisibility
    content: dict | str  # JSON content or string
    parent_id: UUID | None
    order: int
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_category_name(cls, data: Any) -> Any:
        """Extract category name from relationship if available."""
        if isinstance(data, dict):
            return data
        # data is a SQLAlchemy model instance
        if hasattr(data, "category") and data.category:
            # Create a dict with all attributes
            result = {
                "id": data.id,
                "name": data.name,
                "team_id": data.team_id,
                "user_id": data.user_id,
                "category_id": data.category_id,
                "category_name": data.category.name,
                "type": data.type,
                "visibility": data.visibility,
                "content": data.content,
                "parent_id": data.parent_id,
                "order": data.order,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
            return result
        return data

    model_config = {"from_attributes": True}


class TemplateCreateSchema(BaseModel):
    """Schema for creating a template from a document."""

    document_id: UUID
    name: str
    category_name: str
    visibility: TemplateVisibility = TemplateVisibility.TEAM
    include_children: bool = False


class TemplateListSchema(BaseModel):
    """Template schema for list view without content."""

    id: UUID
    name: str
    team_id: UUID
    user_id: UUID
    category_id: UUID
    category_name: str | None = None
    type: TemplateType
    visibility: TemplateVisibility
    parent_id: UUID | None
    order: int
    has_children: bool = False
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_category_name(cls, data: Any) -> Any:
        """Extract category name and check for children if available."""
        if isinstance(data, dict):
            return data
        # data is a SQLAlchemy model instance
        if hasattr(data, "category") and data.category:
            # Create a dict with all attributes except content
            result = {
                "id": data.id,
                "name": data.name,
                "team_id": data.team_id,
                "user_id": data.user_id,
                "category_id": data.category_id,
                "category_name": data.category.name,
                "type": data.type,
                "visibility": data.visibility,
                "parent_id": data.parent_id,
                "order": data.order,
                "has_children": hasattr(data, "children") and len(data.children) > 0,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
            return result
        return data

    model_config = {"from_attributes": True}


class TemplateUpdateSchema(BaseModel):
    """Schema for updating a template."""

    name: str | None = None
    content: dict | str | None = None
    category_name: str | None = None
