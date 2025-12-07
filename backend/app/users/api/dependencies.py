"""Authentication dependencies for API routes."""

from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.projects.repositories import ProjectRepository
from app.users.models import User
from app.users.repositories import ApiTokenRepository


async def get_current_user_from_bearer_token(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to authenticate user via Bearer token.
    Used for MCP authentication.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        Authenticated user

    Raises:
        HTTPException: 401 if token is missing, invalid, or deleted
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )

    token_string = parts[1]

    # Get token from database
    token_repo = ApiTokenRepository(db)
    api_token = await token_repo.get_by_token(token_string)

    if not api_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Check if token is deleted
    if api_token.deleted_at is not None:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    return api_token.user


async def verify_project_access(
    project_id: UUID,
    user: User = Depends(get_current_user_from_bearer_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to verify user has access to a specific project.

    Args:
        project_id: Project ID to check access for
        user: Authenticated user from bearer token
        db: Database session

    Returns:
        User if they have access to the project

    Raises:
        HTTPException: 403 if user doesn't have access to the project
        HTTPException: 404 if project doesn't exist
    """
    project_repo = ProjectRepository(db)
    project = await project_repo.get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user_team_ids = {team.id for team in user.teams}

    if project.team_id not in user_team_ids:
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this project"
        )

    return user
