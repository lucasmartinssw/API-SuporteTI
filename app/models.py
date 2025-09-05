from pydantic import BaseModel

class OperacaoDoisNumeros(BaseModel):
    a: float
    b: float

class User(BaseModel):
    username: str
    password: str 
    full_name: str  = None
    email: str = None
    phone: str = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegistration(BaseModel):
    username: str
    password: str
    cep: str
    numero: str
    complemento: str