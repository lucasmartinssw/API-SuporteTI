from fastapi import FastAPI, HTTPException, APIRouter, Depends
from pydantic import BaseModel
from ..models import User, UserLogin, UserRegistration
from ..auth import get_user, generate_hash, authenticate_user, create_token, get_current_user
from ..database import users
from ..config import ACESS_TOKEN_EXPIRE_MINUTES
from ..viacep import search_cep
from datetime import datetime, timedelta
router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.get("/")
def test():
    return {"message": "Rota de usuários funcionando!"}

@router.post("/register")
def registrar(user: User, usuario = Depends(get_current_user)):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail='Usuário já existe')

    address_data = search_cep(user.cep)
    if 'erro' in address_data:
        raise HTTPException(status_code=400, detail='Invalid CEP')

    hash_password = generate_hash(user.password)
    #chamar viacep
    #adiciomar cep, numero, complemento
    users.insert_one({
        "username": user.username,
        "password": hash_password,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "cep": user.cep,
        "numero": user.numero,
        "complemento": user.complemento,
        "endereco": address_data
    })
    return {"mensagem": "User created!"} 


@router.post("/login")
def login(userLogin: UserLogin):
    if userLogin.username is None or userLogin.password is None:
        raise HTTPException(status_code=400, detail="Username e password são obrigatórios")
    authenticated_user = authenticate_user(userLogin.username, userLogin.password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    acess_token = create_token(data={"sub": authenticated_user['username']}, expires_delta=timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES))
    return {"message": "Usuário logado com sucesso!", "token": acess_token}

@router.get("/users")
def list_users(usuario = Depends(get_current_user)):
    user_list = []
    for user in users.find({}, {"_id": 0, "password": 0}):
        user_list.append(user)
    return user_list

@router.put("/users/{user_username}")
def update_user(user_username: str, user: User, usuario = Depends(get_current_user)):
    existing_user = users.find_one({"username": user_username})
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    address_data = search_cep(user.cep)
    if 'erro' in address_data:
        raise HTTPException(status_code=400, detail='Invalid CEP')

    update_data = {
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "cep": user.cep,
        "numero": user.numero,
        "complemento": user.complemento,
        "endereco": address_data
    }
    if user.password:
        update_data["password"] = generate_hash(user.password)

    users.update_one({"username": user_username}, {"$set": update_data})
    return {"message": "Usuário atualizado com sucesso!"}

@router.delete("/users/{user_username}")
def delete_user(user_username: str, usuario = Depends(get_current_user)):
    existing_user = users.find_one({"username": user_username})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_username == usuario['username']:
        raise HTTPException(status_code=403, detail="User cannot delete themselves")

    users.delete_one({"username": user_username})
    return {"message": "User deleted!"}