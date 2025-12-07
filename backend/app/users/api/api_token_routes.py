"""API token management routes."""

import secrets
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.api.schemas import ApiTokenCreateSchema, ApiTokenSchema
from app.users.api.user_routes import get_current_user_dependency
from app.users.models import ApiToken, User
from app.users.repositories import ApiTokenRepository

router = APIRouter(prefix="/api/v1/api-tokens", tags=["api-tokens"])


def generate_secure_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


@router.get("/", response_model=List[ApiTokenSchema])
async def list_api_tokens(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
) -> List[ApiTokenSchema]:
    """
    List all active API tokens for the authenticated user.
    Returns only non-deleted tokens.
    """
    token_repo = ApiTokenRepository(db)
    tokens = await token_repo.list_user_tokens(current_user.id)

    return [ApiTokenSchema.model_validate(token) for token in tokens]


@router.post("/", response_model=ApiTokenSchema, status_code=201)
async def create_api_token(
    token_data: ApiTokenCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
) -> ApiTokenSchema:
    """
    Create a new API token for the authenticated user.
    """
    token_repo = ApiTokenRepository(db)

    # Generate secure token
    token_value = generate_secure_token()

    # Create token
    api_token = ApiToken(
        name=token_data.name,
        user_id=current_user.id,
        token=token_value,
    )

    created_token = await token_repo.create(api_token)
    await db.commit()
    await db.refresh(created_token)

    return ApiTokenSchema.model_validate(created_token)


@router.delete("/{token_id}", status_code=204)
async def delete_api_token(
    token_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
) -> None:
    """
    Soft delete an API token.
    Only the token owner can delete their tokens.
    """
    token_repo = ApiTokenRepository(db)

    # Get the token
    token = await token_repo.get(token_id)

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Verify ownership
    if token.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own tokens")

    # Check if already deleted
    if token.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Token not found")

    # Soft delete
    await token_repo.soft_delete(token_id)
    await db.commit()
