from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.users.models import TeamRole


class UserBasicSchema(BaseModel):
    """Basic user schema without teams."""

    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    role: TeamRole | None = None  # Role in the context of a specific team

    model_config = {"from_attributes": True}


class TeamSchema(BaseModel):
    """Team schema."""

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamWithMembersSchema(TeamSchema):
    """Team schema with members."""

    members: List[UserBasicSchema] = []


class UserSchema(BaseModel):
    """User schema."""

    id: UUID
    username: str
    email: EmailStr
    teams: List[TeamSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamCreateSchema(BaseModel):
    """Schema for creating a team."""

    name: str


class TeamUpdateSchema(BaseModel):
    """Schema for updating a team."""

    name: str


class GoogleAuthCallbackSchema(BaseModel):
    """Schema for Google OAuth callback."""

    code: str


class AuthResponseSchema(BaseModel):
    """Schema for auth response."""

    user: UserBasicSchema
    message: str = "Authentication successful"


class LocalRegisterSchema(BaseModel):
    """Schema for local registration."""

    email: EmailStr
    password: str


class LocalLoginSchema(BaseModel):
    """Schema for local login."""

    email: EmailStr
    password: str
