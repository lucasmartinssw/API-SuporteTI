from pydantic import BaseModel

class OperacaoDoisNumeros(BaseModel):
    a: float
    b: float

class User(BaseModel):
    name: str
    email: str
    password: str 
    user_type: str

class UserLogin(BaseModel):
    user: str
    password: str

class UserRegistration(BaseModel):
    user: str
    password: str

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    user_type: str | None = None