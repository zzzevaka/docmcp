import enum
from datetime import datetime
from typing import List

from sqlalchemy import UUID as SQLUUID
from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TeamRole(str, enum.Enum):
    """Team member role."""

    MEMBER = "member"
    ADMINISTRATOR = "administrator"


# Create TeamMemberBase using the same registry as Base
# This allows User/Team to find TeamMember when configuring relationships
TeamMemberBase = Base.registry.generate_base()


class TeamMember(TeamMemberBase):
    """Team membership model with role."""

    __tablename__ = "user_team"

    user_id: Mapped[SQLUUID] = mapped_column(SQLUUID, ForeignKey("users.id"), primary_key=True)
    team_id: Mapped[SQLUUID] = mapped_column(SQLUUID, ForeignKey("teams.id"), primary_key=True)
    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole, values_callable=lambda x: [e.value for e in x]),
        default=TeamRole.MEMBER,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="team_memberships", lazy="selectin")
    team: Mapped["Team"] = relationship(back_populates="team_memberships", lazy="selectin")

    def __repr__(self) -> str:
        return f"<TeamMember(user_id={self.user_id}, team_id={self.team_id}, role={self.role})>"


class AuthProvider(str, enum.Enum):
    """Authentication provider."""

    LOCAL = "local"
    GOOGLE = "google"


class User(Base):
    """User model."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    _auth_provider: Mapped[str] = mapped_column(
        "auth_provider", String(20), default="local", nullable=False
    )

    @property
    def auth_provider(self) -> AuthProvider:
        """Get auth provider as enum."""
        return AuthProvider(self._auth_provider)

    @auth_provider.setter
    def auth_provider(self, value: AuthProvider) -> None:
        """Set auth provider from enum."""
        self._auth_provider = value.value

    # Relationships
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )
    api_tokens: Mapped[List["ApiToken"]] = relationship(
        back_populates="user",
        lazy="selectin",
    )

    @property
    def teams(self) -> List["Team"]:
        """Get list of teams this user belongs to."""
        return [membership.team for membership in self.team_memberships]

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email}>"


class Team(Base):
    """Team model."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(64), index=True)

    # Relationships
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def members(self) -> List["User"]:
        """Get list of users in this team."""
        return [membership.user for membership in self.team_memberships]

    def get_member_role(self, user_id: SQLUUID) -> TeamRole | None:
        """Get the role of a specific user in this team."""
        for membership in self.team_memberships:
            if membership.user_id == user_id:
                return membership.role
        return None

    def is_admin(self, user_id: SQLUUID) -> bool:
        """Check if a user is an administrator of this team."""
        return self.get_member_role(user_id) == TeamRole.ADMINISTRATOR

    projects: Mapped[List["Project"]] = relationship(  # noqa: F821
        back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )
    templates: Mapped[List["Template"]] = relationship(  # noqa: F821
        back_populates="team", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name})>"


class Session(Base):
    """Session model for authentication."""

    __tablename__ = "sessions"

    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[SQLUUID] = mapped_column(SQLUUID, ForeignKey("users.id"), index=True)

    # Relationship
    user: Mapped["User"] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id})>"


class InvitationStatus(str, enum.Enum):
    """Status of team invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TeamInvitation(Base):
    """Team invitation model."""

    __tablename__ = "team_invitations"

    team_id: Mapped[SQLUUID] = mapped_column(SQLUUID, ForeignKey("teams.id"), index=True)
    inviter_id: Mapped[SQLUUID] = mapped_column(SQLUUID, ForeignKey("users.id"), index=True)
    invitee_email: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus), default=InvitationStatus.PENDING
    )
    role: Mapped[TeamRole] = mapped_column(
        Enum(TeamRole, values_callable=lambda x: [e.value for e in x]),
        default=TeamRole.MEMBER,
        nullable=False,
    )

    # Relationships
    team: Mapped["Team"] = relationship(lazy="selectin")
    inviter: Mapped["User"] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<TeamInvitation(id={self.id}, team_id={self.team_id}, invitee_email={self.invitee_email}, status={self.status}, role={self.role})>"


class ApiToken(Base):
    """API token model for MCP authentication."""

    __tablename__ = "api_tokens"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    user_id: Mapped[SQLUUID] = mapped_column(SQLUUID, ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="api_tokens", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ApiToken(id={self.id}, name={self.name}, user_id={self.user_id}, deleted_at={self.deleted_at})>"
