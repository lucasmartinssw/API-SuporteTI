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
    username: str
    password: str

class UserRegistration(BaseModel):
    username: str
    password: str
    cep: str
    numero: str
    complemento: str