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
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override to compute archived field from is_archived() method."""
        if hasattr(obj, "is_archived"):
            # Create dict from object
            data = {
                "id": obj.id,
                "name": obj.name,
                "project_id": obj.project_id,
                "type": obj.type,
                "parent_id": obj.parent_id,
                "order": obj.order,
                "editable_by_agent": obj.editable_by_agent,
                "archived": obj.is_archived(),  # Use computed value
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


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
    archived: bool  # Computed: returns true if explicitly archived or inherited from parent
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override to compute archived field from is_archived() method."""
        if hasattr(obj, "is_archived"):
            # Create dict from object
            data = {
                "id": obj.id,
                "name": obj.name,
                "project_id": obj.project_id,
                "type": obj.type,
                "content": obj.content,
                "parent_id": obj.parent_id,
                "order": obj.order,
                "editable_by_agent": obj.editable_by_agent,
                "archived": obj.is_archived(),  # Use computed value
                "created_at": obj.created_at,
                "updated_at": obj.updated_at,
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


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
    archived: bool | None = None
