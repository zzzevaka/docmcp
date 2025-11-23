import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.users.models import Session, Team, User


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


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
