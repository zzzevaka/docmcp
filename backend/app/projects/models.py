import enum
from typing import List, Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import UUID as SQLUUID
from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentType(str, enum.Enum):
    """Document type enum."""

    MARKDOWN = "markdown"
    WHITEBOARD = "whiteboard"


class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(64), index=True)
    team_id: Mapped[UUID_TYPE] = mapped_column(SQLUUID, ForeignKey("teams.id"), index=True)

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="projects", lazy="selectin")  # noqa: F821
    documents: Mapped[List["Document"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, team_id={self.team_id})>"


class Document(Base):
    """Document model."""

    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(128), index=True)
    project_id: Mapped[UUID_TYPE] = mapped_column(SQLUUID, ForeignKey("projects.id"), index=True)
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), index=True)
    content: Mapped[dict] = mapped_column(Text)  # JSON stored as text
    parent_id: Mapped[Optional[UUID_TYPE]] = mapped_column(
        SQLUUID, ForeignKey("documents.id"), nullable=True, index=True
    )
    order: Mapped[int] = mapped_column(default=0, server_default="0", index=True)
    editable_by_agent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    archived: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=None)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="documents", lazy="selectin")
    parent: Mapped[Optional["Document"]] = relationship(
        "Document", remote_side="Document.id", back_populates="children", lazy="selectin"
    )
    children: Mapped[List["Document"]] = relationship(
        "Document", back_populates="parent", cascade="all, delete-orphan", lazy="selectin"
    )

    def is_archived(self) -> bool:
        """Check if document is archived (including inherited from parent)."""
        if self.archived is not None:
            return bool(self.archived)
        if self.parent:
            return self.parent.is_archived()
        return False

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.name}, type={self.type})>"
