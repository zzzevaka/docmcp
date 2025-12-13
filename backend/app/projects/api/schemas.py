from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.projects.models import DocumentType


class ProjectSchema(BaseModel):
    """Project schema."""

    id: UUID
    name: str
    team_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreateSchema(BaseModel):
    """Schema for creating a project."""

    name: str
    team_id: UUID


class ProjectUpdateSchema(BaseModel):
    """Schema for updating a project."""

    name: str


class DocumentListItemSchema(BaseModel):
    """Document schema for list view (without content)."""

    id: UUID
    name: str
    project_id: UUID
    type: DocumentType
    parent_id: UUID | None
    order: int
    editable_by_agent: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentSchema(BaseModel):
    """Document schema."""

    id: UUID
    name: str
    project_id: UUID
    type: DocumentType
    content: dict | str  # JSON content or string
    parent_id: UUID | None
    order: int
    editable_by_agent: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentCreateSchema(BaseModel):
    """Schema for creating a document."""

    name: str
    type: DocumentType
    content: dict | str
    parent_id: UUID | None = None


class DocumentUpdateSchema(BaseModel):
    """Schema for updating a document."""

    name: str | None = None
    content: dict | str | None = None
    parent_id: UUID | None = None
    order: int | None = None
    editable_by_agent: bool | None = None
