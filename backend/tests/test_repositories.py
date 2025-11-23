
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.users.models import Team, User
from app.users.repositories import TeamFilter, TeamRepository, UserRepository


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
async def test_user_repository_create(db_session: AsyncSession) -> None:
    """Test creating a user via repository."""
    repo = UserRepository(db_session)
    user = User(username="testuser", email="test@example.com")

    created_user = await repo.create(user)
    await db_session.commit()

    assert created_user.id is not None
    assert created_user.username == "testuser"


@pytest.mark.asyncio
async def test_user_repository_get(db_session: AsyncSession) -> None:
    """Test getting a user by ID."""
    repo = UserRepository(db_session)
    user = User(username="testuser", email="test@example.com")

    created_user = await repo.create(user)
    await db_session.commit()

    fetched_user = await repo.get(created_user.id)
    assert fetched_user is not None
    assert fetched_user.id == created_user.id
    assert fetched_user.username == "testuser"


@pytest.mark.asyncio
async def test_user_repository_get_by_email(db_session: AsyncSession) -> None:
    """Test getting a user by email."""
    repo = UserRepository(db_session)
    user = User(username="testuser", email="test@example.com")

    await repo.create(user)
    await db_session.commit()

    fetched_user = await repo.get_by_email("test@example.com")
    assert fetched_user is not None
    assert fetched_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_team_repository_create(db_session: AsyncSession) -> None:
    """Test creating a team via repository."""
    repo = TeamRepository(db_session)
    team = Team(name="Test Team")

    created_team = await repo.create(team)
    await db_session.commit()

    assert created_team.id is not None
    assert created_team.name == "Test Team"


@pytest.mark.asyncio
async def test_team_repository_filter_by_user(db_session: AsyncSession) -> None:
    """Test filtering teams by user ID."""
    user_repo = UserRepository(db_session)
    team_repo = TeamRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    team1 = Team(name="Team 1")
    team1.members.append(user)
    await team_repo.create(team1)

    team2 = Team(name="Team 2")
    await team_repo.create(team2)

    await db_session.commit()

    user_teams = await team_repo.find_by_filter(TeamFilter(user_id=user.id))
    assert len(list(user_teams)) == 1
    assert list(user_teams)[0].name == "Team 1"
