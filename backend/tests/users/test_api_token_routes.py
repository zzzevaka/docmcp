"""Tests for API token management routes."""

import pytest
from httpx import AsyncClient

from app.users.models import ApiToken


@pytest.mark.asyncio
async def test_list_api_tokens_empty(client: AsyncClient) -> None:
    """Test listing API tokens when user has none."""
    response = await client.get("/api/v1/api-tokens/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_create_api_token(client: AsyncClient) -> None:
    """Test creating a new API token."""
    response = await client.post(
        "/api/v1/api-tokens/",
        json={"name": "My Test Token"}
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["name"] == "My Test Token"
    assert "token" in data  # Token value should be returned
    assert "created_at" in data
    assert len(data["token"]) > 20  # Should be a long secure token


@pytest.mark.asyncio
async def test_create_api_token_generates_unique_tokens(client: AsyncClient) -> None:
    """Test that each created token has a unique value."""
    response1 = await client.post(
        "/api/v1/api-tokens/",
        json={"name": "Token 1"}
    )
    response2 = await client.post(
        "/api/v1/api-tokens/",
        json={"name": "Token 2"}
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    token1 = response1.json()["token"]
    token2 = response2.json()["token"]

    assert token1 != token2


@pytest.mark.asyncio
async def test_list_api_tokens_with_tokens(client: AsyncClient) -> None:
    """Test listing API tokens when user has some."""
    # Create two tokens
    await client.post("/api/v1/api-tokens/", json={"name": "Token 1"})
    await client.post("/api/v1/api-tokens/", json={"name": "Token 2"})

    # List tokens
    response = await client.get("/api/v1/api-tokens/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Check that token values ARE included in list
    assert "token" in data[0]
    assert "token" in data[1]
    assert len(data[0]["token"]) > 20  # Should be a long secure token
    assert len(data[1]["token"]) > 20

    # Check fields that should be present
    for token in data:
        assert "id" in token
        assert "name" in token
        assert "created_at" in token

    # Check names
    names = [t["name"] for t in data]
    assert "Token 1" in names
    assert "Token 2" in names


@pytest.mark.asyncio
async def test_delete_api_token(client: AsyncClient) -> None:
    """Test soft deleting an API token."""
    # Create a token
    create_response = await client.post(
        "/api/v1/api-tokens/",
        json={"name": "Token to Delete"}
    )
    token_id = create_response.json()["id"]

    # Delete the token
    delete_response = await client.delete(f"/api/v1/api-tokens/{token_id}")
    assert delete_response.status_code == 204

    # Verify it's gone from the list
    list_response = await client.get("/api/v1/api-tokens/")
    tokens = list_response.json()
    token_ids = [t["id"] for t in tokens]
    assert token_id not in token_ids


@pytest.mark.asyncio
async def test_delete_nonexistent_token(client: AsyncClient) -> None:
    """Test deleting a token that doesn't exist."""
    from uuid import uuid4

    fake_id = uuid4()
    response = await client.delete(f"/api/v1/api-tokens/{fake_id}")

    assert response.status_code == 404
    assert "Token not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_already_deleted_token(client: AsyncClient) -> None:
    """Test deleting a token that's already deleted."""
    # Create and delete a token
    create_response = await client.post(
        "/api/v1/api-tokens/",
        json={"name": "Token to Delete Twice"}
    )
    token_id = create_response.json()["id"]

    await client.delete(f"/api/v1/api-tokens/{token_id}")

    # Try to delete again
    response = await client.delete(f"/api/v1/api-tokens/{token_id}")
    assert response.status_code == 404
    assert "Token not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_excludes_deleted_tokens(client: AsyncClient, db_session) -> None:
    """Test that deleted tokens don't appear in the list."""
    from datetime import datetime, timezone

    # Get the test user
    from sqlalchemy import select

    from app.users.models import User
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    # Create a token and immediately soft delete it
    deleted_token = ApiToken(
        name="Deleted Token",
        user_id=user.id,
        token="deleted_token_value",
        deleted_at=datetime.now(timezone.utc)
    )
    db_session.add(deleted_token)
    await db_session.commit()

    # Create an active token via API
    await client.post("/api/v1/api-tokens/", json={"name": "Active Token"})

    # List should only show active token
    response = await client.get("/api/v1/api-tokens/")
    tokens = response.json()

    assert len(tokens) == 1
    assert tokens[0]["name"] == "Active Token"


@pytest.mark.asyncio
async def test_token_value_shown_in_list(client: AsyncClient) -> None:
    """Test that token value is shown both when creating and when listing."""
    # Create a token
    create_response = await client.post(
        "/api/v1/api-tokens/",
        json={"name": "Secret Token"}
    )
    created_token = create_response.json()
    assert "token" in created_token

    # List tokens - token value SHOULD be included
    list_response = await client.get("/api/v1/api-tokens/")
    tokens = list_response.json()

    assert len(tokens) == 1
    assert "token" in tokens[0]
    assert tokens[0]["name"] == "Secret Token"
    assert tokens[0]["token"] == created_token["token"]  # Should be the same token


@pytest.mark.asyncio
async def test_user_can_only_see_their_own_tokens(client: AsyncClient, db_session) -> None:
    """Test that users can only see their own API tokens."""
    from app.users.models import User

    # Create another user
    other_user = User(username="otheruser", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    # Create a token for the other user
    other_token = ApiToken(
        name="Other User Token",
        user_id=other_user.id,
        token="other_user_token"
    )
    db_session.add(other_token)
    await db_session.commit()

    # Create a token for the test user
    await client.post("/api/v1/api-tokens/", json={"name": "My Token"})

    # Test user should only see their own token
    response = await client.get("/api/v1/api-tokens/")
    tokens = response.json()

    assert len(tokens) == 1
    assert tokens[0]["name"] == "My Token"


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_token(client: AsyncClient, db_session) -> None:
    """Test that users cannot delete other users' tokens."""
    from app.users.models import User

    # Create another user with a token
    other_user = User(username="otheruser2", email="other2@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_token = ApiToken(
        name="Other User Token",
        user_id=other_user.id,
        token="other_user_token_2"
    )
    db_session.add(other_token)
    await db_session.commit()
    await db_session.refresh(other_token)

    # Try to delete the other user's token
    response = await client.delete(f"/api/v1/api-tokens/{other_token.id}")

    assert response.status_code == 403
    assert "You can only delete your own tokens" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_token_requires_name(client: AsyncClient) -> None:
    """Test that creating a token requires a name."""
    response = await client.post(
        "/api/v1/api-tokens/",
        json={}
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_multiple_tokens_with_same_name(client: AsyncClient) -> None:
    """Test that users can create multiple tokens with the same name."""
    await client.post("/api/v1/api-tokens/", json={"name": "Same Name"})
    response = await client.post("/api/v1/api-tokens/", json={"name": "Same Name"})

    assert response.status_code == 201

    # Both should exist in the list
    list_response = await client.get("/api/v1/api-tokens/")
    tokens = list_response.json()

    same_name_tokens = [t for t in tokens if t["name"] == "Same Name"]
    assert len(same_name_tokens) == 2
