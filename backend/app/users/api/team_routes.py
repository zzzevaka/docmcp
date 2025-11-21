from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.api.schemas import TeamSchema, TeamCreateSchema, TeamUpdateSchema
from app.users.api.user_routes import get_current_user_dependency
from app.users.models import Team
from app.users.repositories import TeamRepository, TeamFilter

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


@router.get("/", response_model=list[TeamSchema])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> list[TeamSchema]:
    """List teams that the current user belongs to."""
    team_repo = TeamRepository(db)
    teams = await team_repo.find_by_filter(TeamFilter(user_id=current_user.id))
    return [TeamSchema.model_validate(team) for team in teams]


@router.get("/{team_id}", response_model=TeamSchema)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TeamSchema:
    """Get team by ID."""
    team_repo = TeamRepository(db)
    team = await team_repo.get(team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is a member of the team
    if current_user not in team.members:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    return TeamSchema.model_validate(team)


@router.post("/", response_model=TeamSchema, status_code=201)
async def create_team(
    payload: TeamCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TeamSchema:
    """Create a new team."""
    team_repo = TeamRepository(db)

    team = Team(name=payload.name)
    # Add current user as a member
    team.members.append(current_user)

    team = await team_repo.create(team)
    await db.commit()
    await db.refresh(team)

    return TeamSchema.model_validate(team)


@router.patch("/{team_id}", response_model=TeamSchema)
async def update_team(
    team_id: UUID,
    payload: TeamUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TeamSchema:
    """Update a team."""
    team_repo = TeamRepository(db)
    team = await team_repo.get(team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is a member of the team
    if current_user not in team.members:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    team.name = payload.name
    team = await team_repo.update(team)
    await db.commit()
    await db.refresh(team)

    return TeamSchema.model_validate(team)


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> None:
    """Delete a team."""
    team_repo = TeamRepository(db)
    team = await team_repo.get(team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is a member of the team
    if current_user not in team.members:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    await team_repo.delete(team_id)
    await db.commit()
