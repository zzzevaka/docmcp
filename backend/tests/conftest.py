import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import app


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


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Create test client with mocked database and auth."""
    from app.database import get_db
    from app.users.api.user_routes import get_current_user_dependency
    from app.users.models import User

    # Override database dependency
    async def override_get_db():
        yield db_session

    # Create a test user for authentication
    test_user = User(username="testuser", email="test@example.com")
    db_session.add(test_user)
    await db_session.flush()
    # Load teams relationship
    await db_session.refresh(test_user, ["teams"])

    # Override auth dependency
    async def override_get_current_user():
        # Refresh to ensure teams are loaded
        await db_session.refresh(test_user, ["teams"])
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_dependency] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()
