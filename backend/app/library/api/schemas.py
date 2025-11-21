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
    category_id: UUID
    category_name: str | None = None
    type: TemplateType
    content: dict | str  # JSON content or string
    created_at: datetime
    updated_at: datetime

    @model_validator(mode='before')
    @classmethod
    def extract_category_name(cls, data: Any) -> Any:
        """Extract category name from relationship if available."""
        if isinstance(data, dict):
            return data
        # data is a SQLAlchemy model instance
        if hasattr(data, 'category') and data.category:
            # Create a dict with all attributes
            result = {
                'id': data.id,
                'name': data.name,
                'team_id': data.team_id,
                'category_id': data.category_id,
                'category_name': data.category.name,
                'type': data.type,
                'content': data.content,
                'created_at': data.created_at,
                'updated_at': data.updated_at,
            }
            return result
        return data

    model_config = {"from_attributes": True}


class TemplateCreateSchema(BaseModel):
    """Schema for creating a template from a document."""

    document_id: UUID
    name: str
    category_name: str


class TemplateUpdateSchema(BaseModel):
    """Schema for updating a template."""

    name: str | None = None
    content: dict | str | None = None
    category_name: str | None = None
