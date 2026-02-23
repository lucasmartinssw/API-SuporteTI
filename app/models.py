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