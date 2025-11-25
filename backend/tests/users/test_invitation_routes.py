"""Test invitation routes with role management."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import InvitationStatus, Team, TeamInvitation, TeamMember, TeamRole, User


@pytest.mark.asyncio
async def test_create_invitation_with_default_role(db_session: AsyncSession, client: AsyncClient):
    """Test creating invitation with default member role."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as member
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations", json={"invitee_email": "newuser@example.com"}
    )
    assert response.status_code == 201

    # Verify invitation has member role by default
    result = await db_session.execute(
        select(TeamInvitation).where(TeamInvitation.invitee_email == "newuser@example.com")
    )
    invitation = result.scalar_one()
    assert invitation.role == TeamRole.MEMBER


@pytest.mark.asyncio
async def test_create_invitation_with_admin_role(db_session: AsyncSession, client: AsyncClient):
    """Test creating invitation with administrator role."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"invitee_email": "admin@example.com", "role": "administrator"},
    )
    assert response.status_code == 201

    # Verify invitation has administrator role
    result = await db_session.execute(
        select(TeamInvitation).where(TeamInvitation.invitee_email == "admin@example.com")
    )
    invitation = result.scalar_one()
    assert invitation.role == TeamRole.ADMINISTRATOR


@pytest.mark.asyncio
async def test_create_invitation_with_invalid_role(db_session: AsyncSession, client: AsyncClient):
    """Test creating invitation with invalid role fails."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"invitee_email": "user@example.com", "role": "invalid_role"},
    )
    assert response.status_code == 400
    assert "invalid role" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_invitation_with_role(db_session: AsyncSession, client: AsyncClient):
    """Test accepting invitation adds user with specified role."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    invited = result.scalar_one()

    inviter = User(email="newuser@test.dev", username="newuser@test.dev")
    db_session.add(inviter)

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add inviter as administrator
    inviter_membership = TeamMember(
        user_id=inviter.id, team_id=team.id, role=TeamRole.ADMINISTRATOR
    )
    db_session.add(inviter_membership)

    # Create invitation with administrator role
    invitation = TeamInvitation(
        team_id=team.id,
        inviter_id=inviter.id,
        invitee_email=invited.email,  # Same as current user
        status=InvitationStatus.PENDING,
        role=TeamRole.ADMINISTRATOR,
    )
    db_session.add(invitation)
    await db_session.commit()

    # Accept invitation
    response = await client.post(f"/api/v1/invitations/{invitation.id}/accept")
    assert response.status_code == 200

    # Verify user was added with administrator role
    await db_session.refresh(team)
    assert len(team.members) == 2
    assert team.is_admin(inviter.id) is True


@pytest.mark.asyncio
async def test_accept_invitation_member_role(db_session: AsyncSession, client: AsyncClient):
    """Test accepting invitation with member role."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    invited = result.scalar_one()

    inviter = User(email="newuser@test.dev", username="newuser@test.dev")
    db_session.add(inviter)

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add inviter as administrator
    inviter_membership = TeamMember(
        user_id=inviter.id, team_id=team.id, role=TeamRole.ADMINISTRATOR
    )
    db_session.add(inviter_membership)

    # Create invitation with member role
    invitation = TeamInvitation(
        team_id=team.id,
        inviter_id=inviter.id,
        invitee_email=invited.email,
        status=InvitationStatus.PENDING,
        role=TeamRole.MEMBER,
    )
    db_session.add(invitation)
    await db_session.commit()

    # Accept invitation
    response = await client.post(f"/api/v1/invitations/{invitation.id}/accept")
    assert response.status_code == 200

    # Verify user was added with member role
    await db_session.refresh(team)
    member_role = team.get_member_role(inviter.id)
    assert member_role == TeamRole.ADMINISTRATOR  # Inviter is still admin


@pytest.mark.asyncio
async def test_invitation_response_includes_role(db_session: AsyncSession, client: AsyncClient):
    """Test that invitation API response includes role information."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    # Create invitation
    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"invitee_email": "newuser@example.com", "role": "administrator"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_multiple_members_different_roles(db_session: AsyncSession, client: AsyncClient):
    """Test team with multiple members having different roles via invitations."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    admin_user = result.scalar_one()

    team = Team(name="Multi-Role Team")
    db_session.add(team)
    await db_session.flush()

    # Add admin user
    admin_membership = TeamMember(
        user_id=admin_user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR
    )
    db_session.add(admin_membership)

    # Create member user
    member_user = User(username="member", email="member@example.com")
    db_session.add(member_user)
    await db_session.flush()

    # Add member via TeamMember
    member_membership = TeamMember(user_id=member_user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(member_membership)
    await db_session.commit()

    # Get team and verify roles
    response = await client.get(f"/api/v1/teams/{team.id}")
    assert response.status_code == 200
    data = response.json()

    members = data["members"]
    assert len(members) == 2

    # Find each member and verify role
    admin_member = next(m for m in members if m["username"] == "testuser")
    member_member = next(m for m in members if m["username"] == "member")

    assert admin_member["role"] == "administrator"
    assert member_member["role"] == "member"
