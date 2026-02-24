from pydantic import BaseModel, EmailStr
from typing import Optional

class OperacaoDoisNumeros(BaseModel):
    a: float
    b: float

class User(BaseModel):
    name: str
    email: EmailStr # Garante que o formato do email seja válido
    password: str 
    user_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Removi o UserRegistration pois era redundante/não utilizado

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    user_type: Optional[str] = None


class ChamadoCreate(BaseModel):
    title: str
    description: str


class ChamadoOut(BaseModel):
    id: int
    title: str
    description: str
    status: Optional[str] = None
    priority: Optional[str] = None
    user_email: Optional[EmailStr] = None


class MensagemCreate(BaseModel):
    content: str