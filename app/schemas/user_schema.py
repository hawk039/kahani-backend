from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class ForgetPassword(BaseModel):
    email: EmailStr
    new_password: str
    confirmPassword: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    avatar_url: Optional[str] = None # Added field

    class Config:
        from_attributes = True
