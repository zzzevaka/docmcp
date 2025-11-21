from typing import List
import enum

from sqlalchemy import String, ForeignKey, Table, Column, UUID as SQLUUID, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# Association table for User-Team many-to-many relationship
user_team_association = Table(
    "user_team",
    Base.metadata,
    Column("user_id", SQLUUID, ForeignKey("users.id"), primary_key=True),
    Column("team_id", SQLUUID, ForeignKey("teams.id"), primary_key=True),
)


class User(Base):
    """User model."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    # Relationships
    teams: Mapped[List["Team"]] = relationship(
        secondary=user_team_association,
        back_populates="members",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Team(Base):
    """Team model."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(64), index=True)

    # Relationships
    members: Mapped[List["User"]] = relationship(
        secondary=user_team_association,
        back_populates="teams",
    )
    projects: Mapped[List["Project"]] = relationship(  # noqa: F821
        back_populates="team", cascade="all, delete-orphan"
    )
    templates: Mapped[List["Template"]] = relationship(  # noqa: F821
        back_populates="team", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name={self.name})>"


class Session(Base):
    """Session model for authentication."""

    __tablename__ = "sessions"

    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[SQLUUID] = mapped_column(
        SQLUUID, ForeignKey("users.id"), index=True
    )

    # Relationship
    user: Mapped["User"] = relationship()

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
    inviter_id: Mapped[SQLUUID] = mapped_column(
        SQLUUID, ForeignKey("users.id"), index=True
    )
    invitee_email: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(InvitationStatus), default=InvitationStatus.PENDING
    )

    # Relationships
    team: Mapped["Team"] = relationship()
    inviter: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<TeamInvitation(id={self.id}, team_id={self.team_id}, invitee_email={self.invitee_email}, status={self.status})>"
