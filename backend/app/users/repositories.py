from dataclasses import dataclass
from typing import Iterable, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.users.models import InvitationStatus, Session, Team, TeamInvitation, User

ModelT = TypeVar("ModelT")


@dataclass(frozen=True, kw_only=True)
class UserFilter:
    """Filter for user queries."""

    email: str | None = None
    username: str | None = None


@dataclass(frozen=True, kw_only=True)
class TeamFilter:
    """Filter for team queries."""

    user_id: UUID | None = None


@dataclass(frozen=True, kw_only=True)
class TeamInvitationFilter:
    """Filter for team invitation queries."""

    team_id: UUID | None = None
    invitee_email: str | None = None
    status: InvitationStatus | None = None


class UserRepository:
    """Repository for User model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get(self, id_: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == id_).options(selectinload(User.teams))
        )
        return result.scalar_one_or_none()

    async def find_by_filter(self, filter_: UserFilter) -> Iterable[User]:
        """Find users by filter."""
        query = select(User).options(selectinload(User.teams))

        if filter_.email:
            query = query.where(User.email == filter_.email)
        if filter_.username:
            query = query.where(User.username == filter_.username)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        users = await self.find_by_filter(UserFilter(email=email))
        return users[0] if users else None

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> None:
        """Delete a user."""
        user = await self.get(user_id)
        if user:
            await self.db.delete(user)


class TeamRepository:
    """Repository for Team model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get(self, id_: UUID) -> Team | None:
        """Get team by ID."""
        result = await self.db.execute(
            select(Team).where(Team.id == id_).options(selectinload(Team.members))
        )
        return result.scalar_one_or_none()

    async def find_by_filter(self, filter_: TeamFilter) -> Iterable[Team]:
        """Find teams by filter."""
        query = select(Team).options(selectinload(Team.members))

        if filter_.user_id:
            # Filter teams where user is a member
            query = query.join(Team.members).where(User.id == filter_.user_id)

        result = await self.db.execute(query)
        return result.scalars().unique().all()

    async def list_all(self) -> Iterable[Team]:
        """List all teams."""
        result = await self.db.execute(
            select(Team).options(selectinload(Team.members))
        )
        return result.scalars().all()

    async def create(self, team: Team) -> Team:
        """Create a new team."""
        self.db.add(team)
        await self.db.flush()
        await self.db.refresh(team)
        return team

    async def update(self, team: Team) -> Team:
        """Update a team."""
        await self.db.flush()
        await self.db.refresh(team)
        return team

    async def delete(self, team_id: UUID) -> None:
        """Delete a team."""
        team = await self.get(team_id)
        if team:
            await self.db.delete(team)


class SessionRepository:
    """Repository for Session model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get_by_token(self, token: str) -> Session | None:
        """Get session by token."""
        result = await self.db.execute(
            select(Session)
            .where(Session.session_token == token)
            .options(selectinload(Session.user).selectinload(User.teams))
        )
        return result.scalar_one_or_none()

    async def create(self, session: Session) -> Session:
        """Create a new session."""
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def delete(self, session_id: UUID) -> None:
        """Delete a session."""
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session:
            await self.db.delete(session)

    async def delete_by_token(self, token: str) -> None:
        """Delete a session by token."""
        result = await self.db.execute(
            select(Session).where(Session.session_token == token)
        )
        session = result.scalar_one_or_none()
        if session:
            await self.db.delete(session)


class TeamInvitationRepository:
    """Repository for TeamInvitation model."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def get(self, id_: UUID) -> TeamInvitation | None:
        """Get team invitation by ID."""
        result = await self.db.execute(
            select(TeamInvitation)
            .where(TeamInvitation.id == id_)
            .options(selectinload(TeamInvitation.team))
            .options(selectinload(TeamInvitation.inviter))
        )
        return result.scalar_one_or_none()

    async def find_by_filter(
        self, filter_: TeamInvitationFilter
    ) -> Iterable[TeamInvitation]:
        """Find team invitations by filter."""
        query = select(TeamInvitation).options(
            selectinload(TeamInvitation.team),
            selectinload(TeamInvitation.inviter),
        )

        if filter_.team_id:
            query = query.where(TeamInvitation.team_id == filter_.team_id)
        if filter_.invitee_email:
            query = query.where(TeamInvitation.invitee_email == filter_.invitee_email)
        if filter_.status:
            query = query.where(TeamInvitation.status == filter_.status)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, invitation: TeamInvitation) -> TeamInvitation:
        """Create a new team invitation."""
        self.db.add(invitation)
        await self.db.flush()
        await self.db.refresh(invitation)
        return invitation

    async def update(self, invitation: TeamInvitation) -> TeamInvitation:
        """Update a team invitation."""
        await self.db.flush()
        await self.db.refresh(invitation)
        return invitation

    async def delete(self, invitation_id: UUID) -> None:
        """Delete a team invitation."""
        invitation = await self.get(invitation_id)
        if invitation:
            await self.db.delete(invitation)
