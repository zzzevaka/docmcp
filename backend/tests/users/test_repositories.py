import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import ApiToken, Team, TeamMember, User
from app.users.repositories import (
    ApiTokenFilter,
    ApiTokenRepository,
    TeamFilter,
    TeamRepository,
    UserRepository,
)


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
    await team_repo.create(team1)
    await team_repo.create(TeamMember(user=user, team=team1))

    team2 = Team(name="Team 2")
    await team_repo.create(team2)

    await db_session.commit()

    user_teams = await team_repo.find_by_filter(TeamFilter(user_id=user.id))
    assert len(list(user_teams)) == 1
    assert list(user_teams)[0].name == "Team 1"


@pytest.mark.asyncio
async def test_api_token_repository_create(db_session: AsyncSession) -> None:
    """Test creating an API token via repository."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)
    await db_session.commit()

    token = ApiToken(name="My Token", user_id=user.id, token="test_token_123")
    created_token = await token_repo.create(token)
    await db_session.commit()

    assert created_token.id is not None
    assert created_token.name == "My Token"
    assert created_token.token == "test_token_123"
    assert created_token.deleted_at is None


@pytest.mark.asyncio
async def test_api_token_repository_get(db_session: AsyncSession) -> None:
    """Test getting an API token by ID."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    token = ApiToken(name="My Token", user_id=user.id, token="test_token_123")
    created_token = await token_repo.create(token)
    await db_session.commit()

    fetched_token = await token_repo.get(created_token.id)
    assert fetched_token is not None
    assert fetched_token.id == created_token.id
    assert fetched_token.name == "My Token"
    assert fetched_token.user.username == "testuser"


@pytest.mark.asyncio
async def test_api_token_repository_get_by_token(db_session: AsyncSession) -> None:
    """Test getting an API token by token string."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    token = ApiToken(name="My Token", user_id=user.id, token="test_token_123")
    await token_repo.create(token)
    await db_session.commit()

    fetched_token = await token_repo.get_by_token("test_token_123")
    assert fetched_token is not None
    assert fetched_token.token == "test_token_123"
    assert fetched_token.name == "My Token"
    assert fetched_token.user.username == "testuser"


@pytest.mark.asyncio
async def test_api_token_repository_list_user_tokens(db_session: AsyncSession) -> None:
    """Test listing active tokens for a user."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    token1 = ApiToken(name="Token 1", user_id=user.id, token="token_1")
    token2 = ApiToken(name="Token 2", user_id=user.id, token="token_2")
    await token_repo.create(token1)
    await token_repo.create(token2)
    await db_session.commit()

    tokens = await token_repo.list_user_tokens(user.id)
    token_list = list(tokens)
    assert len(token_list) == 2
    token_names = [t.name for t in token_list]
    assert "Token 1" in token_names
    assert "Token 2" in token_names


@pytest.mark.asyncio
async def test_api_token_repository_soft_delete(db_session: AsyncSession) -> None:
    """Test soft deleting an API token."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    token = ApiToken(name="My Token", user_id=user.id, token="test_token_123")
    created_token = await token_repo.create(token)
    await db_session.commit()

    # Soft delete
    deleted_token = await token_repo.soft_delete(created_token.id)
    await db_session.commit()

    assert deleted_token is not None
    assert deleted_token.deleted_at is not None

    # Verify it doesn't appear in active tokens list
    active_tokens = await token_repo.list_user_tokens(user.id)
    assert len(list(active_tokens)) == 0


@pytest.mark.asyncio
async def test_api_token_repository_filter_excludes_deleted(db_session: AsyncSession) -> None:
    """Test that find_by_filter excludes deleted tokens by default."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    token1 = ApiToken(name="Active Token", user_id=user.id, token="active_token")
    token2 = ApiToken(name="Deleted Token", user_id=user.id, token="deleted_token")
    await token_repo.create(token1)
    created_token2 = await token_repo.create(token2)
    await db_session.commit()

    # Soft delete token2
    await token_repo.soft_delete(created_token2.id)
    await db_session.commit()

    # Filter should exclude deleted tokens by default
    tokens = await token_repo.find_by_filter(ApiTokenFilter(user_id=user.id))
    token_list = list(tokens)
    assert len(token_list) == 1
    assert token_list[0].name == "Active Token"


@pytest.mark.asyncio
async def test_api_token_repository_filter_include_deleted(db_session: AsyncSession) -> None:
    """Test that find_by_filter can include deleted tokens."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    token1 = ApiToken(name="Active Token", user_id=user.id, token="active_token")
    token2 = ApiToken(name="Deleted Token", user_id=user.id, token="deleted_token")
    await token_repo.create(token1)
    created_token2 = await token_repo.create(token2)
    await db_session.commit()

    # Soft delete token2
    await token_repo.soft_delete(created_token2.id)
    await db_session.commit()

    # Filter with include_deleted=True should return both
    tokens = await token_repo.find_by_filter(ApiTokenFilter(user_id=user.id, include_deleted=True))
    token_list = list(tokens)
    assert len(token_list) == 2
    token_names = [t.name for t in token_list]
    assert "Active Token" in token_names
    assert "Deleted Token" in token_names


@pytest.mark.asyncio
async def test_api_token_repository_filter_by_token_string(db_session: AsyncSession) -> None:
    """Test filtering by token string."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user = User(username="testuser", email="test@example.com")
    user = await user_repo.create(user)

    token1 = ApiToken(name="Token 1", user_id=user.id, token="specific_token")
    token2 = ApiToken(name="Token 2", user_id=user.id, token="another_token")
    await token_repo.create(token1)
    await token_repo.create(token2)
    await db_session.commit()

    tokens = await token_repo.find_by_filter(ApiTokenFilter(token="specific_token"))
    token_list = list(tokens)
    assert len(token_list) == 1
    assert token_list[0].name == "Token 1"


@pytest.mark.asyncio
async def test_api_token_repository_different_users_tokens(db_session: AsyncSession) -> None:
    """Test that list_user_tokens only returns tokens for the specified user."""
    user_repo = UserRepository(db_session)
    token_repo = ApiTokenRepository(db_session)

    user1 = User(username="user1", email="user1@example.com")
    user2 = User(username="user2", email="user2@example.com")
    user1 = await user_repo.create(user1)
    user2 = await user_repo.create(user2)

    token1 = ApiToken(name="User 1 Token", user_id=user1.id, token="user1_token")
    token2 = ApiToken(name="User 2 Token", user_id=user2.id, token="user2_token")
    await token_repo.create(token1)
    await token_repo.create(token2)
    await db_session.commit()

    user1_tokens = await token_repo.list_user_tokens(user1.id)
    user1_token_list = list(user1_tokens)
    assert len(user1_token_list) == 1
    assert user1_token_list[0].name == "User 1 Token"

    user2_tokens = await token_repo.list_user_tokens(user2.id)
    user2_token_list = list(user2_tokens)
    assert len(user2_token_list) == 1
    assert user2_token_list[0].name == "User 2 Token"
