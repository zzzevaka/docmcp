import secrets
from typing import Dict, Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.users.models import User, Session, AuthProvider, Team
from app.users.repositories import UserRepository, SessionRepository, UserFilter, TeamRepository
from app.users.utils.password import hash_password, verify_password


class AuthService:
    """Service for handling authentication."""

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self.user_repo = UserRepository(db_session)
        self.session_repo = SessionRepository(db_session)
        self.team_repo = TeamRepository(db_session)

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

    async def _create_default_team(self, user: User) -> Team:
        """Create a default team for a new user."""
        # Refresh user with teams relationship loaded
        await self.db.refresh(user, attribute_names=["teams"])

        team = Team(name=user.email)
        team = await self.team_repo.create(team)

        # Add user to the team
        user.teams.append(team)
        await self.db.flush()
        return team

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

            # Create default team for new user
            await self._create_default_team(user)

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

    async def register_local_user(self, email: str, password: str) -> User:
        """Register a new local user with email and password."""
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Use email as username (ensure uniqueness with suffix if needed)
        username = email
        existing_users = await self.user_repo.find_by_filter(
            UserFilter(username=username)
        )
        if existing_users:
            # Append random suffix to make it unique
            username = f"{email}_{secrets.token_hex(4)}"

        # Hash password and create user
        password_hash = hash_password(password)
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            auth_provider=AuthProvider.LOCAL,
        )
        user = await self.user_repo.create(user)

        # Create default team for new user
        await self._create_default_team(user)

        return user

    async def login_local_user(self, email: str, password: str) -> User:
        """Authenticate a local user with email and password."""
        user = await self.user_repo.get_by_email(email)

        if not user:
            raise ValueError("Invalid email or password")

        if user.auth_provider != AuthProvider.LOCAL:
            raise ValueError(
                f"This account uses {user.auth_provider.value} authentication"
            )

        if not user.password_hash:
            raise ValueError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        return user
