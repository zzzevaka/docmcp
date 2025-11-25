import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import Session, Team, TeamMember, TeamRole, User


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Test user creation."""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_create_team(db_session: AsyncSession) -> None:
    """Test team creation."""
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)

    assert team.id is not None
    assert team.name == "Test Team"
    assert team.created_at is not None
    assert team.updated_at is not None


@pytest.mark.asyncio
async def test_user_team_relationship(db_session: AsyncSession) -> None:
    """Test many-to-many relationship between users and teams."""
    user = User(username="testuser", email="test@example.com")
    team = Team(name="Test Team")

    db_session.add(user)
    db_session.add(team)
    await db_session.flush()

    # Add user to team via TeamMember
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)

    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(team)

    assert len(team.members) == 1
    assert team.members[0].username == "testuser"
    assert len(user.teams) == 1
    assert user.teams[0].name == "Test Team"


@pytest.mark.asyncio
async def test_create_session(db_session: AsyncSession) -> None:
    """Test session creation."""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    await db_session.flush()

    session = Session(session_token="test_token_123", user_id=user.id)
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.id is not None
    assert session.session_token == "test_token_123"
    assert session.user_id == user.id


@pytest.mark.asyncio
async def test_team_member_with_role(db_session: AsyncSession) -> None:
    """Test creating team membership with role."""
    user = User(username="testuser", email="test@example.com")
    team = Team(name="Test Team")

    db_session.add(user)
    db_session.add(team)
    await db_session.flush()

    # Add user as member
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.commit()
    await db_session.refresh(team)
    await db_session.refresh(user)

    assert len(team.team_memberships) == 1
    assert team.team_memberships[0].role == TeamRole.MEMBER
    assert len(team.members) == 1
    assert team.members[0].username == "testuser"


@pytest.mark.asyncio
async def test_team_member_administrator_role(db_session: AsyncSession) -> None:
    """Test creating team membership with administrator role."""
    user = User(username="admin", email="admin@example.com")
    team = Team(name="Admin Team")

    db_session.add(user)
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()
    await db_session.refresh(team)

    assert len(team.team_memberships) == 1
    assert team.team_memberships[0].role == TeamRole.ADMINISTRATOR


@pytest.mark.asyncio
async def test_team_get_member_role(db_session: AsyncSession) -> None:
    """Test getting member role from team."""
    user = User(username="testuser", email="test@example.com")
    team = Team(name="Test Team")

    db_session.add(user)
    db_session.add(team)
    await db_session.flush()

    # Add user as administrator
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(team_member)
    await db_session.commit()
    await db_session.refresh(team)

    role = team.get_member_role(user.id)
    assert role == TeamRole.ADMINISTRATOR


@pytest.mark.asyncio
async def test_team_is_admin(db_session: AsyncSession) -> None:
    """Test checking if user is admin of team."""
    admin_user = User(username="admin", email="admin@example.com")
    member_user = User(username="member", email="member@example.com")
    team = Team(name="Test Team")

    db_session.add(admin_user)
    db_session.add(member_user)
    db_session.add(team)
    await db_session.flush()

    # Add admin
    admin_membership = TeamMember(
        user_id=admin_user.id, team_id=team.id, role=TeamRole.ADMINISTRATOR
    )
    db_session.add(admin_membership)

    # Add member
    member_membership = TeamMember(user_id=member_user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(member_membership)

    await db_session.commit()
    await db_session.refresh(team)

    assert team.is_admin(admin_user.id) is True
    assert team.is_admin(member_user.id) is False


@pytest.mark.asyncio
async def test_team_multiple_members_with_roles(db_session: AsyncSession) -> None:
    """Test team with multiple members having different roles."""
    user1 = User(username="admin", email="admin@example.com")
    user2 = User(username="member1", email="member1@example.com")
    user3 = User(username="member2", email="member2@example.com")
    team = Team(name="Multi Member Team")

    db_session.add(user1)
    db_session.add(user2)
    db_session.add(user3)
    db_session.add(team)
    await db_session.flush()

    # Add admin
    TeamMember(user_id=user1.id, team_id=team.id, role=TeamRole.ADMINISTRATOR)
    db_session.add(TeamMember(user_id=user1.id, team_id=team.id, role=TeamRole.ADMINISTRATOR))

    # Add members
    db_session.add(TeamMember(user_id=user2.id, team_id=team.id, role=TeamRole.MEMBER))
    db_session.add(TeamMember(user_id=user3.id, team_id=team.id, role=TeamRole.MEMBER))

    await db_session.commit()
    await db_session.refresh(team)

    assert len(team.members) == 3
    assert team.is_admin(user1.id) is True
    assert team.is_admin(user2.id) is False
    assert team.is_admin(user3.id) is False
