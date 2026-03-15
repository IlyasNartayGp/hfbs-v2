from pydantic import BaseModel, EmailStr
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
