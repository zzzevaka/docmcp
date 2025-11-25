import enum
from typing import List, Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import UUID as SQLUUID
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TemplateVisibility(str, enum.Enum):
    """Template visibility enum."""

    PRIVATE = "private"  # Only visible to the creator
    TEAM = "team"  # Visible to team members
    PUBLIC = "public"  # Visible to everyone


class TemplateType(str, enum.Enum):
    """Template type enum (mirrors DocumentType)."""

    MARKDOWN = "markdown"
    WHITEBOARD = "whiteboard"


class Category(Base):
    """Category model for organizing templates."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    visibility: Mapped[TemplateVisibility] = mapped_column(
        Enum(TemplateVisibility), default=TemplateVisibility.PUBLIC
    )

    # Relationships
    templates: Mapped[List["Template"]] = relationship(
        back_populates="category", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name})>"


class Template(Base):
    """Template model - similar to Document but stored in library."""

    __tablename__ = "templates"

    name: Mapped[str] = mapped_column(String(128), index=True)
    team_id: Mapped[UUID_TYPE] = mapped_column(SQLUUID, ForeignKey("teams.id"), index=True)
    user_id: Mapped[UUID_TYPE] = mapped_column(SQLUUID, ForeignKey("users.id"), index=True)
    category_id: Mapped[UUID_TYPE] = mapped_column(SQLUUID, ForeignKey("categories.id"), index=True)
    type: Mapped[TemplateType] = mapped_column(Enum(TemplateType), index=True)
    visibility: Mapped[TemplateVisibility] = mapped_column(
        Enum(TemplateVisibility), default=TemplateVisibility.TEAM, index=True
    )
    content: Mapped[dict] = mapped_column(Text)  # JSON stored as text
    parent_id: Mapped[Optional[UUID_TYPE]] = mapped_column(
        SQLUUID, ForeignKey("templates.id"), nullable=True, index=True
    )
    order: Mapped[int] = mapped_column(default=0, server_default="0", index=True)

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="templates", lazy="selectin")  # noqa: F821
    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
    category: Mapped["Category"] = relationship(back_populates="templates", lazy="selectin")
    parent: Mapped[Optional["Template"]] = relationship(
        "Template", remote_side="Template.id", back_populates="children", lazy="selectin"
    )
    children: Mapped[List["Template"]] = relationship(
        "Template", back_populates="parent", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name={self.name}, type={self.type})>"
