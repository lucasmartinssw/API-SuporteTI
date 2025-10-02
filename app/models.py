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
    cep: str
    numero: str
    complemento: str