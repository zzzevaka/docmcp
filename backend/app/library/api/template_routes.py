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
from app.library.repositories import CategoryRepository, TemplateRepository
from app.projects.repositories import DocumentRepository
from app.users.api.user_routes import get_current_user_dependency

router = APIRouter(prefix="/api/v1/library/templates", tags=["library", "templates"])


@router.get("/", response_model=list[TemplateListSchema])
async def list_templates(
    category_name: str | None = Query(None, description="Filter by category name"),
    only_root: bool = Query(
        True, description="If true, only return root templates (without parent)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> list[TemplateListSchema]:
    """List templates, optionally filtered by category.

    By default only returns root templates (parent_id is null).
    Set only_root=false to get all templates including children.
    """
    template_repo = TemplateRepository(db)
    category_repo = CategoryRepository(db)

    # Get category_id if filtering by category
    category_id = None
    if category_name:
        category = await category_repo.get_by_name(category_name)
        if category:
            category_id = category.id

    # Get user teams
    user_team_ids = [team.id for team in current_user.teams]

    # Filter templates by visibility in database
    templates = await template_repo.find_visible_for_user(
        user_id=current_user.id,
        user_team_ids=user_team_ids,
        category_id=category_id,
        include_content=False,
        only_root=only_root,
    )

    return [TemplateListSchema.model_validate(t) for t in templates]


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

    # User can access template if:
    # 1. It's public
    # 2. It's team visibility and user is in the team
    # 3. It's private and user is the creator
    if template.visibility == TemplateVisibility.PUBLIC:
        pass  # Everyone can access
    elif template.visibility == TemplateVisibility.TEAM:
        if template.team_id not in user_team_ids:
            raise HTTPException(status_code=403, detail="Cannot access this template")
    elif template.visibility == TemplateVisibility.PRIVATE:
        if template.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot access this template")

    return TemplateSchema.model_validate(template)


async def _create_template_from_document(
    document,
    name: str,
    category_id: UUID,
    visibility: TemplateVisibility,
    parent_template_id: UUID | None,
    user_id: UUID,
    template_repo: TemplateRepository,
    document_repo: DocumentRepository,
    order: int = 0,
) -> Template:
    """Helper function to create a template from a document."""
    # Convert document content to appropriate format
    content = document.content
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            pass

    # Map document type to template type
    template_type = (
        TemplateType.MARKDOWN if document.type.value == "markdown" else TemplateType.WHITEBOARD
    )

    # Create template
    template = Template(
        name=name,
        team_id=document.project.team_id,
        user_id=user_id,
        category_id=category_id,
        type=template_type,
        visibility=visibility,
        content=json.dumps(content) if isinstance(content, dict) else content,
        parent_id=parent_template_id,
        order=order,
    )

    template = await template_repo.create(template)
    return template


async def _create_template_with_children(
    document,
    name: str,
    category_id: UUID,
    visibility: TemplateVisibility,
    parent_template_id: UUID | None,
    user_id: UUID,
    template_repo: TemplateRepository,
    document_repo: DocumentRepository,
    db: AsyncSession,
    order: int = 0,
) -> Template:
    """Recursively create templates from a document and its children."""
    # Create template for current document
    template = await _create_template_from_document(
        document=document,
        name=name,
        category_id=category_id,
        visibility=visibility,
        parent_template_id=parent_template_id,
        user_id=user_id,
        template_repo=template_repo,
        document_repo=document_repo,
        order=order,
    )

    # Explicitly refresh document to load children relationship
    await db.refresh(document, ["children"])

    # Recursively create templates for children
    if document.children:
        for idx, child_doc in enumerate(sorted(document.children, key=lambda d: d.order)):
            await _create_template_with_children(
                document=child_doc,
                name=child_doc.name,
                category_id=category_id,
                visibility=visibility,
                parent_template_id=template.id,
                user_id=user_id,
                template_repo=template_repo,
                document_repo=document_repo,
                db=db,
                order=idx,
            )

    return template


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

    # Create template (and children if requested)
    if payload.include_children:
        template = await _create_template_with_children(
            document=document,
            name=payload.name,
            category_id=category.id,
            visibility=payload.visibility,
            parent_template_id=None,
            user_id=current_user.id,
            template_repo=template_repo,
            document_repo=document_repo,
            db=db,
        )
    else:
        template = await _create_template_from_document(
            document=document,
            name=payload.name,
            category_id=category.id,
            visibility=payload.visibility,
            parent_template_id=None,
            user_id=current_user.id,
            template_repo=template_repo,
            document_repo=document_repo,
        )

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
