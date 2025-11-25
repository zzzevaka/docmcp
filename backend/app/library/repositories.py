from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, selectinload

from app.library.models import Category, Template, TemplateType, TemplateVisibility
from app.users.models import Team, TeamMember


@dataclass(frozen=True, kw_only=True)
class TemplateFilter:
    """Filter for template queries."""

    team_id: UUID | None = None
    category_id: UUID | None = None
    type: TemplateType | None = None
    visibility: TemplateVisibility | None = None


class CategoryRepository:
    """Repository for Category model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get(self, id_: UUID) -> Category | None:
        """Get category by ID."""
        result = await self.db.execute(
            select(Category).where(Category.id == id_).options(selectinload(Category.templates))
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Category | None:
        """Get category by name."""
        result = await self.db.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> Iterable[Category]:
        """List all categories."""
        result = await self.db.execute(select(Category))
        return result.scalars().all()

    async def create(self, category: Category) -> Category:
        """Create a new category."""
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def get_or_create(
        self, name: str, visibility: TemplateVisibility = TemplateVisibility.PUBLIC
    ) -> Category:
        """Get category by name or create if doesn't exist."""
        category = await self.get_by_name(name)
        if not category:
            category = Category(name=name, visibility=visibility)
            category = await self.create(category)
        return category

    async def update(self, category: Category) -> Category:
        """Update a category."""
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: UUID) -> None:
        """Delete a category."""
        category = await self.get(category_id)
        if category:
            await self.db.delete(category)


class TemplateRepository:
    """Repository for Template model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get(self, id_: UUID) -> Template | None:
        """Get template by ID."""
        result = await self.db.execute(
            select(Template)
            .where(Template.id == id_)
            .options(
                selectinload(Template.team)
                .selectinload(Team.team_memberships)
                .selectinload(TeamMember.user),
                selectinload(Template.category),
                selectinload(Template.children),
            )
        )
        return result.scalar_one_or_none()

    async def get_with_hierarchy(self, id_: UUID) -> Template | None:
        """Get template by ID with full hierarchy of children loaded."""
        template = await self.get(id_)
        if template:
            await self._load_children_recursive(template)
        return template

    async def _load_children_recursive(self, template: Template) -> None:
        """Recursively load all children for a template."""
        # Force load children if not already loaded
        await self.db.refresh(template, ["children"])

        # Recursively load children's children
        for child in template.children:
            await self._load_children_recursive(child)

    async def find_by_filter(self, filter_: TemplateFilter) -> Iterable[Template]:
        """Find templates by filter."""
        query = select(Template).options(
            selectinload(Template.team)
            .selectinload(Team.team_memberships)
            .selectinload(TeamMember.user),
            selectinload(Template.category),
        )

        if filter_.team_id:
            query = query.where(Template.team_id == filter_.team_id)
        if filter_.category_id:
            query = query.where(Template.category_id == filter_.category_id)
        if filter_.type:
            query = query.where(Template.type == filter_.type)

        # Order by created_at
        query = query.order_by(Template.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def find_visible_for_user(
        self,
        user_id: UUID,
        user_team_ids: list[UUID],
        category_id: UUID | None = None,
        include_content: bool = True,
        only_root: bool = True,
    ) -> Iterable[Template]:
        """Find templates visible to a specific user based on visibility rules.

        User can see templates that are:
        1. Public (visible to everyone)
        2. Team visibility and user is in the team
        3. Private and user is the creator

        Args:
            only_root: If True, only return root templates (parent_id is null)
        """
        query = select(Template)

        if not include_content:
            query = query.options(defer(Template.content))

        query = query.options(
            selectinload(Template.team)
            .selectinload(Team.team_memberships)
            .selectinload(TeamMember.user),
            selectinload(Template.category),
            selectinload(Template.children),
        )

        # Build visibility filter using OR conditions
        visibility_conditions = [
            Template.visibility == TemplateVisibility.PUBLIC,
            (Template.visibility == TemplateVisibility.TEAM)
            & (Template.team_id.in_(user_team_ids)),
            (Template.visibility == TemplateVisibility.PRIVATE) & (Template.user_id == user_id),
        ]

        query = query.where(or_(*visibility_conditions))

        # Filter only root templates (without parent)
        if only_root:
            query = query.where(Template.parent_id.is_(None))

        # Apply category filter if provided
        if category_id:
            query = query.where(Template.category_id == category_id)

        # Order by created_at
        query = query.order_by(Template.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_all(self) -> Iterable[Template]:
        """List all templates."""
        result = await self.db.execute(
            select(Template).options(
                selectinload(Template.team)
                .selectinload(Team.team_memberships)
                .selectinload(TeamMember.user),
                selectinload(Template.category),
            )
        )
        return result.scalars().all()

    async def create(self, template: Template) -> Template:
        """Create a new template."""
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update(self, template: Template) -> Template:
        """Update a template."""
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete(self, template_id: UUID) -> None:
        """Delete a template."""
        template = await self.get(template_id)
        if template:
            await self.db.delete(template)
