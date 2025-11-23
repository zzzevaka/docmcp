import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.library.api.schemas import (
    TemplateCreateSchema,
    TemplateListSchema,
    TemplateSchema,
    TemplateUpdateSchema,
)
from app.library.models import Template, TemplateType, TemplateVisibility
from app.library.repositories import CategoryRepository, TemplateFilter, TemplateRepository
from app.projects.repositories import DocumentRepository
from app.users.api.user_routes import get_current_user_dependency

router = APIRouter(prefix="/api/v1/library/templates", tags=["library", "templates"])


@router.get("/", response_model=list[TemplateListSchema])
async def list_templates(
    category_name: str | None = Query(None, description="Filter by category name"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> list[TemplateListSchema]:
    """List templates, optionally filtered by category."""
    template_repo = TemplateRepository(db)
    category_repo = CategoryRepository(db)

    # Build filter
    filter_params = {}

    if category_name:
        category = await category_repo.get_by_name(category_name)
        if category:
            filter_params["category_id"] = category.id

    templates = await template_repo.find_by_filter_without_content(TemplateFilter(**filter_params))

    # Filter templates by visibility - user can see:
    # 1. Public templates
    # 2. Team templates from their own teams
    user_team_ids = [team.id for team in current_user.teams]
    visible_templates = [
        t for t in templates
        if t.category.visibility == TemplateVisibility.PUBLIC or t.team_id in user_team_ids
    ]

    return [TemplateListSchema.model_validate(t) for t in visible_templates]


@router.get("/{template_id}", response_model=TemplateSchema)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TemplateSchema:
    """Get template by ID."""
    template_repo = TemplateRepository(db)
    template = await template_repo.get(template_id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check visibility permissions
    user_team_ids = [team.id for team in current_user.teams]
    if template.category.visibility == TemplateVisibility.TEAM and template.team_id not in user_team_ids:
        raise HTTPException(status_code=403, detail="Cannot access this template")

    return TemplateSchema.model_validate(template)


@router.post("/", response_model=TemplateSchema, status_code=201)
async def create_template(
    payload: TemplateCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TemplateSchema:
    """Create a new template from a document."""
    document_repo = DocumentRepository(db)
    template_repo = TemplateRepository(db)
    category_repo = CategoryRepository(db)

    # Get the document
    document = await document_repo.get(payload.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if user is member of the document's project team
    if document.project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this document's project team")

    # Get or create category
    category = await category_repo.get_or_create(payload.category_name)

    # Convert document content to appropriate format
    content = document.content
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            pass

    # Map document type to template type
    template_type = TemplateType.MARKDOWN if document.type.value == "markdown" else TemplateType.WHITEBOARD

    # Create template
    template = Template(
        name=payload.name,
        team_id=document.project.team_id,
        category_id=category.id,
        type=template_type,
        content=json.dumps(content) if isinstance(content, dict) else content,
    )

    template = await template_repo.create(template)
    await db.commit()

    # Reload template to get relationships (including category)
    template = await template_repo.get(template.id)

    return TemplateSchema.model_validate(template)


@router.put("/{template_id}", response_model=TemplateSchema)
async def update_template(
    template_id: UUID,
    payload: TemplateUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TemplateSchema:
    """Update a template."""
    template_repo = TemplateRepository(db)
    category_repo = CategoryRepository(db)

    template = await template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Only team members can update the template
    if template.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Only the owning team can update this template")

    # Update fields
    if payload.name is not None:
        template.name = payload.name

    if payload.content is not None:
        content = payload.content
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                pass
        template.content = json.dumps(content) if isinstance(content, dict) else content

    if payload.category_name is not None:
        category = await category_repo.get_or_create(payload.category_name)
        template.category_id = category.id

    template = await template_repo.update(template)
    await db.commit()

    # Reload template to get relationships (including category)
    template = await template_repo.get(template_id)

    return TemplateSchema.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> None:
    """Delete a template."""
    template_repo = TemplateRepository(db)

    template = await template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Only team members can delete the template
    if template.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Only the owning team can delete this template")

    await template_repo.delete(template_id)
    await db.commit()
