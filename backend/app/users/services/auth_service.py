import secrets
from typing import Dict, Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.users.models import User, Session
from app.users.repositories import UserRepository, SessionRepository, UserFilter


class AuthService:
    """Service for handling authentication."""

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.user_repo = UserRepository(db_session)
        self.session_repo = SessionRepository(db_session)

    async def exchange_google_code(
        self, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange Google authorization code for access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    async def get_or_create_user(
        self, email: str, username: str | None = None
    ) -> User:
        """Get existing user by email or create a new one."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Extract username from email if not provided
            if not username:
                username = email.split("@")[0]

            # Ensure username is unique
            existing_users = await self.user_repo.find_by_filter(
                UserFilter(username=username)
            )
            if existing_users:
                # Append random suffix to make it unique
                username = f"{username}_{secrets.token_hex(4)}"

            user = User(email=email, username=username)
            user = await self.user_repo.create(user)

        return user

    async def create_session(self, user_id: UUID) -> str:
        """Create a new session for a user."""
        session_token = secrets.token_urlsafe(32)
        session = Session(session_token=session_token, user_id=user_id)
        await self.session_repo.create(session)
        return session_token

    async def get_user_by_session(self, session_token: str) -> User | None:
        """Get user by session token."""
        session = await self.session_repo.get_by_token(session_token)
        return session.user if session else None

    async def delete_session(self, session_token: str) -> None:
        """Delete a session."""
        await self.session_repo.delete_by_token(session_token)
