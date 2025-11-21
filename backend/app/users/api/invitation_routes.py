from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.api.auth_routes import get_current_user
from app.users.models import User, TeamInvitation, InvitationStatus
from app.users.repositories import TeamRepository, TeamInvitationRepository, TeamInvitationFilter, UserRepository

router = APIRouter(prefix="/api/v1", tags=["invitations"])


# Request/Response schemas
class InvitationCreate(BaseModel):
    """Schema for creating a team invitation."""

    invitee_email: EmailStr


class InvitationResponse(BaseModel):
    """Schema for team invitation response."""

    id: UUID
    team_id: UUID
    team_name: str
    inviter_id: UUID
    inviter_email: str
    invitee_email: str
    status: InvitationStatus
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# Create team invitation
@router.post(
    "/teams/{team_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    team_id: UUID,
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """Create a team invitation."""
    team_repo = TeamRepository(db)
    invitation_repo = TeamInvitationRepository(db)

    # Check if team exists and user is a member
    team = await team_repo.get(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if current_user.id not in [member.id for member in team.members]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    # Check if invitation already exists
    existing_invitations = await invitation_repo.find_by_filter(
        TeamInvitationFilter(
            team_id=team_id,
            invitee_email=invitation_data.invitee_email,
            status=InvitationStatus.PENDING,
        )
    )
    if existing_invitations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already exists for this email",
        )

    # Create invitation
    invitation = TeamInvitation(
        team_id=team_id,
        inviter_id=current_user.id,
        invitee_email=invitation_data.invitee_email,
        status=InvitationStatus.PENDING,
    )
    invitation = await invitation_repo.create(invitation)
    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        team_id=invitation.team_id,
        team_name=invitation.team.name,
        inviter_id=invitation.inviter_id,
        inviter_email=invitation.inviter.email,
        invitee_email=invitation.invitee_email,
        status=invitation.status,
        created_at=invitation.created_at.isoformat(),
        updated_at=invitation.updated_at.isoformat(),
    )


# List team invitations
@router.get("/teams/{team_id}/invitations", response_model=list[InvitationResponse])
async def list_team_invitations(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InvitationResponse]:
    """List all invitations for a team."""
    team_repo = TeamRepository(db)
    invitation_repo = TeamInvitationRepository(db)

    # Check if team exists and user is a member
    team = await team_repo.get(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    if current_user.id not in [member.id for member in team.members]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    invitations = await invitation_repo.find_by_filter(
        TeamInvitationFilter(team_id=team_id)
    )

    return [
        InvitationResponse(
            id=inv.id,
            team_id=inv.team_id,
            team_name=inv.team.name,
            inviter_id=inv.inviter_id,
            inviter_email=inv.inviter.email,
            invitee_email=inv.invitee_email,
            status=inv.status,
            created_at=inv.created_at.isoformat(),
            updated_at=inv.updated_at.isoformat(),
        )
        for inv in invitations
    ]


# Get pending invitations for current user
@router.get("/invitations/me", response_model=list[InvitationResponse])
async def get_my_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InvitationResponse]:
    """Get pending invitations for current user."""
    invitation_repo = TeamInvitationRepository(db)

    invitations = await invitation_repo.find_by_filter(
        TeamInvitationFilter(
            invitee_email=current_user.email,
            status=InvitationStatus.PENDING,
        )
    )

    return [
        InvitationResponse(
            id=inv.id,
            team_id=inv.team_id,
            team_name=inv.team.name,
            inviter_id=inv.inviter_id,
            inviter_email=inv.inviter.email,
            invitee_email=inv.invitee_email,
            status=inv.status,
            created_at=inv.created_at.isoformat(),
            updated_at=inv.updated_at.isoformat(),
        )
        for inv in invitations
    ]


# Accept invitation
@router.post("/invitations/{invitation_id}/accept", response_model=InvitationResponse)
async def accept_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """Accept a team invitation."""
    invitation_repo = TeamInvitationRepository(db)
    team_repo = TeamRepository(db)
    user_repo = UserRepository(db)

    invitation = await invitation_repo.get(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.invitee_email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation is not for you",
        )

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation is not pending",
        )

    # Add user to team
    team = await team_repo.get(invitation.team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    # Refresh user with teams relationship
    user = await user_repo.get(current_user.id)
    if user and team:
        user.teams.append(team)
        await db.flush()

    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED
    invitation = await invitation_repo.update(invitation)
    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        team_id=invitation.team_id,
        team_name=invitation.team.name,
        inviter_id=invitation.inviter_id,
        inviter_email=invitation.inviter.email,
        invitee_email=invitation.invitee_email,
        status=invitation.status,
        created_at=invitation.created_at.isoformat(),
        updated_at=invitation.updated_at.isoformat(),
    )


# Reject invitation
@router.post("/invitations/{invitation_id}/reject", response_model=InvitationResponse)
async def reject_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """Reject a team invitation."""
    invitation_repo = TeamInvitationRepository(db)

    invitation = await invitation_repo.get(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.invitee_email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation is not for you",
        )

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation is not pending",
        )

    # Update invitation status
    invitation.status = InvitationStatus.REJECTED
    invitation = await invitation_repo.update(invitation)
    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        team_id=invitation.team_id,
        team_name=invitation.team.name,
        inviter_id=invitation.inviter_id,
        inviter_email=invitation.inviter.email,
        invitee_email=invitation.invitee_email,
        status=invitation.status,
        created_at=invitation.created_at.isoformat(),
        updated_at=invitation.updated_at.isoformat(),
    )
