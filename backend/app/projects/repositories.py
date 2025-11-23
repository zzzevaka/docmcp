from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.projects.models import Document, DocumentType, Project
from app.users.models import Team


@dataclass(frozen=True, kw_only=True)
class ProjectFilter:
    """Filter for project queries."""

    team_id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class DocumentFilter:
    """Filter for document queries."""

    project_id: UUID | None = None
    parent_id: UUID | None = None
    type: DocumentType | None = None


class ProjectRepository:
    """Repository for Project model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get(self, id_: UUID) -> Project | None:
        """Get project by ID."""
        result = await self.db.execute(
            select(Project)
            .where(Project.id == id_)
            .options(selectinload(Project.team).selectinload(Team.members))
        )
        return result.scalar_one_or_none()

    async def find_by_filter(self, filter_: ProjectFilter) -> Iterable[Project]:
        """Find projects by filter."""
        query = select(Project).options(
            selectinload(Project.team).selectinload(Team.members)
        )

        if filter_.team_id:
            query = query.where(Project.team_id == filter_.team_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_all(self) -> Iterable[Project]:
        """List all projects."""
        result = await self.db.execute(
            select(Project).options(selectinload(Project.team).selectinload(Team.members))
        )
        return result.scalars().all()

    async def create(self, project: Project) -> Project:
        """Create a new project."""
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        """Update a project."""
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: UUID) -> None:
        """Delete a project."""
        project = await self.get(project_id)
        if project:
            await self.db.delete(project)


class DocumentRepository:
    """Repository for Document model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get(self, id_: UUID) -> Document | None:
        """Get document by ID."""
        result = await self.db.execute(
            select(Document)
            .where(Document.id == id_)
            .options(
                selectinload(Document.project).selectinload(Project.team),
                selectinload(Document.children),
                selectinload(Document.parent),
            )
        )
        return result.scalar_one_or_none()

    async def find_by_filter(self, filter_: DocumentFilter) -> Iterable[Document]:
        """Find documents by filter."""
        query = select(Document).options(
            selectinload(Document.project).selectinload(Project.team),
            selectinload(Document.children),
            selectinload(Document.parent),
        )

        if filter_.project_id:
            query = query.where(Document.project_id == filter_.project_id)
        if filter_.parent_id is not None:
            query = query.where(Document.parent_id == filter_.parent_id)
        if filter_.type:
            query = query.where(Document.type == filter_.type)

        # Order by order field, then by created_at
        query = query.order_by(Document.order, Document.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_for_project(self, project_id: UUID) -> Iterable[Document]:
        """List all documents for a project."""
        return await self.find_by_filter(DocumentFilter(project_id=project_id))

    async def create(self, document: Document) -> Document:
        """Create a new document."""
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def update(self, document: Document) -> Document:
        """Update a document."""
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def delete(self, document_id: UUID) -> None:
        """Delete a document."""
        document = await self.get(document_id)
        if document:
            await self.db.delete(document)
