"""Test team routes with role management."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import Team, TeamMember, TeamRole, User


@pytest.mark.asyncio
async def test_create_team_creates_admin(db_session: AsyncSession, client: AsyncClient):
    """Test that creating a team makes the creator an administrator."""
    from uuid import UUID

    response = await client.post("/api/v1/teams/", json={"name": "New Team"})
    assert response.status_code == 201
    data = response.json()

    # Convert string UUID to UUID object
    team_id = UUID(data["id"]) if isinstance(data["id"], str) else data["id"]

    # Verify user is admin
    result = await db_session.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one()
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    await db_session.refresh(team)
    assert team.is_admin(user.id) is True


@pytest.mark.asyncio
async def test_get_team_returns_member_roles(db_session: AsyncSession, client: AsyncClient):
    """Test that getting a team returns members with their roles."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    response = await client.get(f"/api/v1/teams/{team.id}")
    assert response.status_code == 200
    data = response.json()

    assert len(data["members"]) == 1
    assert data["members"][0]["role"] == "administrator"
    assert data["members"][0]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_remove_member_requires_admin(db_session: AsyncSession, client: AsyncClient):
    """Test that only administrators can remove members."""
    # Create team with current user as member (not admin)
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    current_user = result.scalar_one()

    other_user = User(username="other", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add current user as member (not admin)
    team_member = TeamMember(user_id=current_user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)

    # Add other user as member
    other_member = TeamMember(user_id=other_user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(other_member)
    await db_session.commit()

    # Try to remove other user (should fail)
    response = await client.delete(f"/api/v1/teams/{team.id}/members/{other_user.id}")
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_remove_self(db_session: AsyncSession, client: AsyncClient):
    """Test that users cannot remove themselves from a team."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    # Try to remove self
    response = await client.delete(f"/api/v1/teams/{team.id}/members/{user.id}")
    assert response.status_code == 400
    assert "cannot remove yourself" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_can_remove_member(db_session: AsyncSession, client: AsyncClient):
    """Test that administrators can remove other members."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    admin_user = result.scalar_one()

    member_user = User(username="member", email="member@example.com")
    db_session.add(member_user)
    await db_session.flush()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add admin user as administrator
    admin_membership = TeamMember(
        user_id=admin_user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR
    )
    db_session.add(admin_membership)

    # Add other user as member
    member_membership = TeamMember(user_id=member_user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(member_membership)
    await db_session.commit()

    # Remove member as admin
    response = await client.delete(f"/api/v1/teams/{team.id}/members/{member_user.id}")
    assert response.status_code == 204

    # Verify member was removed
    await db_session.refresh(team)
    assert len(team.members) == 1
    assert team.members[0].id == admin_user.id


@pytest.mark.asyncio
async def test_update_team_requires_admin(db_session: AsyncSession, client: AsyncClient):
    """Test that only administrators can update team settings."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Original Name")
    db_session.add(team)
    await db_session.flush()

    # Add user as member (not admin)
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.commit()

    # Try to update team
    response = await client.patch(f"/api/v1/teams/{team.id}", json={"name": "New Name"})
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_can_update_team(db_session: AsyncSession, client: AsyncClient):
    """Test that administrators can update team settings."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Original Name")
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    # Update team
    response = await client.patch(f"/api/v1/teams/{team.id}", json={"name": "New Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_team_requires_admin(db_session: AsyncSession, client: AsyncClient):
    """Test that only administrators can delete teams."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as member (not admin)
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.commit()

    # Try to delete team
    response = await client.delete(f"/api/v1/teams/{team.id}")
    assert response.status_code == 403
    assert "administrators" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_can_delete_team(db_session: AsyncSession, client: AsyncClient):
    """Test that administrators can delete teams."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()

    team_id = team.id

    # Delete team
    response = await client.delete(f"/api/v1/teams/{team_id}")
    assert response.status_code == 204

    # Verify team was deleted
    result = await db_session.execute(select(Team).where(Team.id == team_id))
    deleted_team = result.scalar_one_or_none()
    assert deleted_team is None
