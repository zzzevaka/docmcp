from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.api.schemas import (
    TeamCreateSchema,
    TeamSchema,
    TeamUpdateSchema,
    TeamWithMembersSchema,
)
from app.users.api.user_routes import get_current_user_dependency
from app.users.models import Team, TeamMember, TeamRole
from app.users.repositories import TeamFilter, TeamRepository, UserRepository

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


@router.get("/{team_id}", response_model=TeamWithMembersSchema)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TeamWithMembersSchema:
    """Get team by ID."""
    from app.users.api.schemas import UserBasicSchema

    team_repo = TeamRepository(db)
    team = await team_repo.get(team_id)

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if user is a member of the team
    if current_user not in team.members:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    # Build team response with member roles
    team_data = {
        "id": team.id,
        "name": team.name,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": [
            UserBasicSchema(
                id=membership.user.id,
                username=membership.user.username,
                email=membership.user.email,
                created_at=membership.user.created_at,
                updated_at=membership.user.updated_at,
                role=membership.role,
            )
            for membership in team.team_memberships
        ],
    }

    return TeamWithMembersSchema(**team_data)


@router.post("/", response_model=TeamSchema, status_code=201)
async def create_team(
    payload: TeamCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> TeamSchema:
    """Create a new team."""
    team_repo = TeamRepository(db)

    team = Team(name=payload.name)
    team = await team_repo.create(team)
    await db.flush()

    # Add current user as an administrator
    team_member = TeamMember(
        user_id=current_user.id,
        team_id=team.id,
        role=TeamRole.ADMINISTRATOR,
    )
    db.add(team_member)

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

    # Check if user is an administrator
    if not team.is_admin(current_user.id):
        raise HTTPException(status_code=403, detail="Only administrators can update team settings")

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

    # Check if user is an administrator
    if not team.is_admin(current_user.id):
        raise HTTPException(status_code=403, detail="Only administrators can delete the team")

    await team_repo.delete(team_id)
    await db.commit()


@router.delete("/{team_id}/members/{user_id}", status_code=204)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> None:
    """Remove a member from a team."""
    team_repo = TeamRepository(db)
    user_repo = UserRepository(db)

    team = await team_repo.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if current user is a member of the team
    if current_user not in team.members:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    # Check if user is an administrator
    if not team.is_admin(current_user.id):
        raise HTTPException(status_code=403, detail="Only administrators can remove members")

    # Prevent users from removing themselves
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot remove yourself from the team")

    # Get the user to remove
    user_to_remove = await user_repo.get(user_id)
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user is a member of the team
    if user_to_remove not in team.members:
        raise HTTPException(status_code=404, detail="User is not a member of this team")

    # Remove the team membership
    from sqlalchemy import delete

    from app.users.models import TeamMember

    await db.execute(
        delete(TeamMember).where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
    )
    await db.commit()
