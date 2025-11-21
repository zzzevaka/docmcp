import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.projects.api.schemas import (
    DocumentSchema,
    DocumentCreateSchema,
    DocumentUpdateSchema,
)
from app.projects.models import Document
from app.projects.repositories import ProjectRepository, DocumentRepository
from app.users.api.user_routes import get_current_user_dependency

router = APIRouter(prefix="/api/v1/projects", tags=["documents"])


@router.get("/{project_id}/documents/", response_model=list[DocumentSchema])
async def list_documents(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> list[DocumentSchema]:
    """List documents for a project."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists and user has access
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    # Get documents
    documents = await document_repo.list_for_project(project_id)

    # Parse content if stored as string
    result = []
    for doc in documents:
        doc_dict = DocumentSchema.model_validate(doc).model_dump()
        # Parse JSON content if it's a string
        if isinstance(doc_dict["content"], str):
            try:
                doc_dict["content"] = json.loads(doc_dict["content"])
            except json.JSONDecodeError:
                pass
        result.append(DocumentSchema(**doc_dict))

    return result


@router.get("/{project_id}/documents/{document_id}", response_model=DocumentSchema)
async def get_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> DocumentSchema:
    """Get document by ID."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists and user has access
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    # Get document
    document = await document_repo.get(document_id)
    if not document or document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Parse content
    doc_dict = DocumentSchema.model_validate(document).model_dump()
    if isinstance(doc_dict["content"], str):
        try:
            doc_dict["content"] = json.loads(doc_dict["content"])
        except json.JSONDecodeError:
            pass

    return DocumentSchema(**doc_dict)


@router.post("/{project_id}/documents/", response_model=DocumentSchema, status_code=201)
async def create_document(
    project_id: UUID,
    payload: DocumentCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> DocumentSchema:
    """Create a new document."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists and user has access
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    # If parent_id is provided, check if parent exists
    if payload.parent_id:
        parent = await document_repo.get(payload.parent_id)
        if not parent or parent.project_id != project_id:
            raise HTTPException(status_code=404, detail="Parent document not found")

    # Store content as JSON string
    content_str = (
        json.dumps(payload.content)
        if isinstance(payload.content, dict)
        else payload.content
    )

    # Create document
    document = Document(
        name=payload.name,
        project_id=project_id,
        type=payload.type,
        content=content_str,
        parent_id=payload.parent_id,
    )
    document = await document_repo.create(document)
    await db.commit()
    await db.refresh(document)

    # Parse content for response
    doc_dict = DocumentSchema.model_validate(document).model_dump()
    if isinstance(doc_dict["content"], str):
        try:
            doc_dict["content"] = json.loads(doc_dict["content"])
        except json.JSONDecodeError:
            pass

    return DocumentSchema(**doc_dict)


@router.put("/{project_id}/documents/{document_id}", response_model=DocumentSchema)
async def update_document(
    project_id: UUID,
    document_id: UUID,
    payload: DocumentUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> DocumentSchema:
    """Update a document."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists and user has access
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    # Get document
    document = await document_repo.get(document_id)
    if not document or document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update fields - use model_dump to check which fields were actually set
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        document.name = payload.name

    if "content" in update_data:
        content_str = (
            json.dumps(payload.content)
            if isinstance(payload.content, dict)
            else payload.content
        )
        document.content = content_str

    if "parent_id" in update_data:
        # Validate that the parent exists and is in the same project
        if payload.parent_id:
            parent = await document_repo.get(payload.parent_id)
            if not parent or parent.project_id != project_id:
                raise HTTPException(status_code=400, detail="Invalid parent document")
            # Prevent circular references
            if payload.parent_id == document_id:
                raise HTTPException(status_code=400, detail="Document cannot be its own parent")
        document.parent_id = payload.parent_id

    if "order" in update_data:
        document.order = payload.order

    document = await document_repo.update(document)
    await db.commit()
    await db.refresh(document)

    # Parse content for response
    doc_dict = DocumentSchema.model_validate(document).model_dump()
    if isinstance(doc_dict["content"], str):
        try:
            doc_dict["content"] = json.loads(doc_dict["content"])
        except json.JSONDecodeError:
            pass

    return DocumentSchema(**doc_dict)


@router.delete("/{project_id}/documents/{document_id}", status_code=204)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> None:
    """Delete a document."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists and user has access
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    # Get document
    document = await document_repo.get(document_id)
    if not document or document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    await document_repo.delete(document_id)
    await db.commit()
