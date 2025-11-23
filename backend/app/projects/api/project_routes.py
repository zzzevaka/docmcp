from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.projects.api.schemas import (
    ProjectCreateSchema,
    ProjectSchema,
    ProjectUpdateSchema,
)
from app.projects.models import Project
from app.projects.repositories import ProjectRepository
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
