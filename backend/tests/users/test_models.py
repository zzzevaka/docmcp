import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import Session, Team, User


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

    team.members.append(user)

    db_session.add(team)
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
