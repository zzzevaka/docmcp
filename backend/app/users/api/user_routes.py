from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.api.schemas import UserSchema
from app.users.repositories import UserRepository
from app.users.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


async def get_current_user_dependency(
    session_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Dependency to get current authenticated user."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_session(session_token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    return user


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> UserSchema:
    """Get user by ID."""
    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserSchema.model_validate(user)
