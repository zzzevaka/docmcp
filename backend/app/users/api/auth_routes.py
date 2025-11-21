from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.users.api.schemas import GoogleAuthCallbackSchema, AuthResponseSchema, UserSchema
from app.users.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/google/callback", response_model=AuthResponseSchema)
async def google_callback(
    payload: GoogleAuthCallbackSchema,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponseSchema:
    """Handle Google OAuth callback."""
    auth_service = AuthService(db)

    try:
        # Exchange code for access token
        token_data = await auth_service.exchange_google_code(
            payload.code, payload.redirect_uri
        )
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")

        # Get user info from Google
        user_info = await auth_service.get_google_user_info(access_token)
        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")

        # Get or create user
        user = await auth_service.get_or_create_user(email=email, username=name)

        # Create session
        session_token = await auth_service.create_session(user.id)

        # Set secure HTTP-only cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=settings.app_env != "dev",  # Use secure cookie in production
            samesite="lax",
            max_age=30 * 24 * 60 * 60,  # 30 days
        )

        await db.commit()

        return AuthResponseSchema(user=UserSchema.model_validate(user))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/logout")
async def logout(
    response: Response,
    session_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Logout user."""
    if session_token:
        auth_service = AuthService(db)
        await auth_service.delete_session(session_token)
        await db.commit()

    # Clear cookie
    response.delete_cookie(key="session_token")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserSchema)
async def get_current_user(
    session_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> UserSchema:
    """Get current authenticated user."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_session(session_token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    return UserSchema.model_validate(user)
