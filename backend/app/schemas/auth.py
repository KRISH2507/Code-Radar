from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: Optional[str] = None


class SignupResponse(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class GoogleAuthRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResendOTPRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    is_verified: bool
    plan: str = "free"
    role: str = "user"
    scan_count: int = 0
    scan_reset_date: Optional[date] = None

    class Config:
        from_attributes = True
