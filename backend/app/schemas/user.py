"""
User and authentication Pydantic schemas.
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRoleEnum(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: Optional[str] = None
    theme: str = "light"


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str  # This will be the email
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: UserRoleEnum = UserRoleEnum.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Schema for user update."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    theme: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=100)


# Token Schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


# API Key Schemas
class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    can_ingest: bool = True
    can_read: bool = True
    can_analyze: bool = False
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    can_ingest: bool
    can_read: bool
    can_analyze: bool
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime


class APIKeyCreatedResponse(APIKeyResponse):
    """Response when API key is created (includes key value)."""
    api_key: str = Field(description="The API key value. Only shown once!")
