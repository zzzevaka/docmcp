import json
import zipfile
from datetime import datetime
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.projects.api.schemas import (
    ProjectCreateSchema,
    ProjectSchema,
    ProjectUpdateSchema,
)
from app.projects.models import DocumentType, Project
from app.projects.repositories import DocumentRepository, ProjectRepository
from app.users.api.user_routes import get_current_user_dependency
from app.users.repositories import TeamRepository

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectSchema])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> list[ProjectSchema]:
    """List projects for teams the current user belongs to."""
    project_repo = ProjectRepository(db)

    # Get all projects for user's teams
    user_team_ids = [team.id for team in current_user.teams]
    all_projects = []

    for team_id in user_team_ids:
        from app.projects.repositories import ProjectFilter

        projects = await project_repo.find_by_filter(ProjectFilter(team_id=team_id))
        all_projects.extend(projects)

    return [ProjectSchema.model_validate(p) for p in all_projects]


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> ProjectSchema:
    """Get project by ID."""
    project_repo = ProjectRepository(db)
    project = await project_repo.get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if user is member of the project's team
    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    return ProjectSchema.model_validate(project)


@router.post("/", response_model=ProjectSchema, status_code=201)
async def create_project(
    payload: ProjectCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> ProjectSchema:
    """Create a new project."""
    team_repo = TeamRepository(db)
    project_repo = ProjectRepository(db)

    # Check if team exists
    team = await team_repo.get(payload.team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is member of the team
    if team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    # Create project
    project = Project(name=payload.name, team_id=payload.team_id)
    project = await project_repo.create(project)
    await db.commit()
    await db.refresh(project)

    return ProjectSchema.model_validate(project)


@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> ProjectSchema:
    """Update a project."""
    project_repo = ProjectRepository(db)
    project = await project_repo.get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if user is member of the project's team
    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    # Update project
    project.name = payload.name
    project = await project_repo.update(project)
    await db.commit()
    await db.refresh(project)

    return ProjectSchema.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> None:
    """Delete a project."""
    project_repo = ProjectRepository(db)
    project = await project_repo.get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if user is member of the project's team
    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    await project_repo.delete(project_id)
    await db.commit()


def _add_documents_to_zip(
    zip_file: zipfile.ZipFile,
    documents: list,
    parent_id: UUID | None,
    path: str,
    used_names: dict | None = None,
) -> None:
    """Recursively add documents to ZIP maintaining hierarchy."""
    if used_names is None:
        used_names = {}

    # Filter documents for current level
    current_level_docs = [doc for doc in documents if doc.parent_id == parent_id]

    # Sort by order
    current_level_docs.sort(key=lambda d: d.order)

    for doc in current_level_docs:
        # Parse content
        content = doc.content
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = {"raw": content}

        # Determine file extension and content based on document type
        if doc.type == DocumentType.MARKDOWN:
            file_extension = ".md"
            file_content = content.get("markdown", "")
        elif doc.type == DocumentType.WHITEBOARD:
            file_extension = ".excalidraw"
            # For Excalidraw, we export the raw JSON
            file_content = json.dumps(content.get("raw", {}), indent=2)
        else:
            continue  # Skip unknown types

        # Sanitize filename (remove invalid characters)
        safe_filename = "".join(
            c for c in doc.name if c.isalnum() or c in (" ", "-", "_", ".")
        ).strip()

        # Handle empty names
        if not safe_filename:
            safe_filename = "untitled"

        # Handle duplicate names at the same level
        base_name = safe_filename
        counter = 1
        full_path_key = f"{path}{safe_filename}"
        while full_path_key in used_names:
            safe_filename = f"{base_name}_{counter}"
            full_path_key = f"{path}{safe_filename}"
            counter += 1

        used_names[full_path_key] = True

        # Build full path for file
        file_path = f"{path}{safe_filename}{file_extension}"

        # Add file to ZIP
        zip_file.writestr(file_path, file_content)

        # Recursively add children in a subdirectory
        child_path = f"{path}{safe_filename}/"
        _add_documents_to_zip(zip_file, documents, parent_id=doc.id, path=child_path, used_names=used_names)


@router.get("/{project_id}/export")
async def export_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> StreamingResponse:
    """Export all project documents as a ZIP archive."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists and user has access
    project = await project_repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.team not in current_user.teams:
        raise HTTPException(status_code=403, detail="Not a member of this project's team")

    # Get all documents for the project
    documents = await document_repo.list_for_project(project_id)

    # Check if there are any documents
    if not documents:
        raise HTTPException(status_code=400, detail="No documents to export")

    # Create ZIP archive in memory
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Build document tree and add files
        _add_documents_to_zip(zip_file, documents, parent_id=None, path="")

    # Prepare response
    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project.name}_export_{timestamp}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
