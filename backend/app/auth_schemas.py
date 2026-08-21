from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    organization_name: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    organization_id: str
    organization_name: str
