from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int

class RefreshTokenResponse(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)