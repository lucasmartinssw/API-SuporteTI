from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta
from ..models import User, UserLogin
from ..auth import generate_hash, verify_password, create_token, get_current_user
from ..database import cursor, conn
from ..config import ACESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.get("/")
def test():
    return {"message": "Router Users is working!"}

@router.get("/users")
def list_users(current_user: dict = Depends(get_current_user)):
    cursor.execute("SELECT name, email FROM user")
    users = cursor.fetchall()
    return users

@router.post("/register")
def registrar(user: User):
    cursor.execute("SELECT * FROM user WHERE name = %s", (user.name,))
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = generate_hash(user.password)

    
    cursor.execute(
        "INSERT INTO user (name, email, password, user_type, create_date) VALUES (%s, %s, %s, %s, NOW())",
        (user.name, user.email, hashed_password, user.user_type)
    )
    conn.commit()

    return {"message": "User created!"}

@router.post("/login")
def login(userLogin: UserLogin):
    # CORRIGIDO: Buscar por 'name'
    cursor.execute("SELECT * FROM user WHERE name = %s", (userLogin.name,))
    user_data = cursor.fetchone()

    if not user_data or not verify_password(userLogin.password, user_data['password']):
        raise HTTPException(status_code=401, detail="Invalid name or password")

    expires_delta = timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES)
    # CORRIGIDO: Passar o 'name' do usuário para o token
    token_data = {"sub": user_data['name']}
    token = create_token(data=token_data, expires_delta=expires_delta)

    return {"message": "Usuário logado com sucesso!", "token": token, "token_type": "bearer"}

@router.put("/{user_name}") # ALTERADO: parâmetro da rota
def update_user(user_name: str, user: User, current_user: dict = Depends(get_current_user)):
    # CORRIGIDO: Buscar por 'name'
    cursor.execute("SELECT * FROM user WHERE name = %s", (user_name,))
    existing_user = cursor.fetchone()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = generate_hash(user.password)

    
    cursor.execute(
        "UPDATE user SET email = %s, password = %s WHERE name = %s",
        (user.email, hashed_password, user_name)
    )
    conn.commit()

    return {"message": "User updated!"}

@router.delete("/{user_name}")
def delete_user(user_name: str, current_user: dict = Depends(get_current_user)):
    cursor.execute("SELECT * FROM user WHERE name = %s", (user_name,))
    existing_user = cursor.fetchone()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("DELETE FROM user WHERE name = %s", (user_name,))
    conn.commit()

    return {"message": "User deleted!"}