from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegistration(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    updated_at: datetime

class UserLogout(BaseModel):
    message: str = "User logged out successfully"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str  = "Bearer"


class TokenRequest(BaseModel):
    token: str


