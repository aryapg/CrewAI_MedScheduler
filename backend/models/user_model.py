"""
User data models for authentication and user management.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class UserCreate(BaseModel):
    """Model for creating a new user."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: UserRole = UserRole.PATIENT
    phone: Optional[str] = None
    specialty: Optional[str] = None  # For doctors


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Model for user response (excluding sensitive data)."""
    id: str
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    specialty: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

