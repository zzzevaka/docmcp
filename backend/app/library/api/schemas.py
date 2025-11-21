from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

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
    type: TemplateType
    content: dict | str  # JSON content or string
    created_at: datetime
    updated_at: datetime

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
