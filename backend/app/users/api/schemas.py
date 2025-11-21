from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserSchema(BaseModel):
    """User schema."""

    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamSchema(BaseModel):
    """Team schema."""

    id: UUID
    name: str
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
    redirect_uri: str


class AuthResponseSchema(BaseModel):
    """Schema for auth response."""

    user: UserSchema
    message: str = "Authentication successful"
