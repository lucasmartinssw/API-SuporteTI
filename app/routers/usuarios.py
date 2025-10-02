from fastapi import APIRouter, HTTPException, Depends
from ..models import User, UserLogin
from ..auth import generate_hash, authenticate_user, create_token, get_current_user
from ..database import cursor, conn  # importa o cursor e conexão do database.py

router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.get("/")
def test():
    return {"message": "Router Users is working!"}

@router.get("/users")
def list_users():
    cursor.execute("SELECT name, email FROM user")
    users = cursor.fetchall()
    return users

@router.post("/register")
def registrar(user: User):
    # Verifica se usuário já existe
    cursor.execute("SELECT * FROM user WHERE name = %s", (user.name,))
    existing_user = cursor.fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Cria hash da senha
    hashed_password = generate_hash(user.password)

    # Insere novo usuário
    cursor.execute(
        "INSERT INTO user (name, email, password, user_type) VALUES (%s, %s, %s, %s)",
        (user.name, user.email, hashed_password, user.user_type)
    )
    conn.commit()

    return {"message": "User created!"}

@router.post("/login")
def login(userLogin: UserLogin):
    cursor.execute("SELECT * FROM user WHERE username = %s", (userLogin.username,))
    user_data = cursor.fetchone()
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not authenticate_user(userLogin.password, user_data['password']):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(user_data['username'])

    return {"message": "Usuário logado com sucesso!", "token": token}

@router.put("/{user_username}")
def update_user(user_username: str, user: User, current_user=Depends(get_current_user)):
    cursor.execute("SELECT * FROM user WHERE username = %s", (user_username,))
    existing_user = cursor.fetchone()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = generate_hash(user.password)

    cursor.execute(
        "UPDATE user SET email = %s, password = %s WHERE username = %s",
        (user.email, hashed_password, user_username)
    )
    conn.commit()

    return {"message": "User updated!"}

@router.delete("/{user_username}")
def delete_user(user_username: str, current_user=Depends(get_current_user)):
    cursor.execute("SELECT * FROM user WHERE username = %s", (user_username,))
    existing_user = cursor.fetchone()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("DELETE FROM user WHERE username = %s", (user_username,))
    conn.commit()

    return {"message": "User deleted!"}