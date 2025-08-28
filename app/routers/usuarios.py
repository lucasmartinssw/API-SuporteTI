from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from ..models import User, UserLogin
from ..auth import get_user, generate_hash
router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.get("/")
def test():
    return {"message": "Rota de usuários funcionando!"}

router.post("/register")
def registrar(user: User):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail='Usuário já existe')

    hash_password = generate_hash(user.password)

    return {"mensagem": "OK!" , "hash" : hash_password} 


@router.post("/login")
def login(userLogin: UserLogin):
    return {"message": "Route to login user"}