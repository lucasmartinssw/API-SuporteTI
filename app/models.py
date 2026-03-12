from pydantic import BaseModel, EmailStr
from typing import Optional


class User(BaseModel):
    name: str
    email: EmailStr
    password: str
    user_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    user_type: Optional[str] = None


class ChamadoCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    category: str = "Outros"


class MensagemCreate(BaseModel):
    content: str