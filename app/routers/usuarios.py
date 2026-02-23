from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
from ..models import User, UserLogin, UserUpdate
from ..auth import generate_hash, verify_password, create_token, get_current_user
from ..database import get_db_cursor, get_db_connection # Importe as dependências recomendadas
from ..config import ACESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.get("/test") # Mudado para não conflitar com a listagem principal
def test():
    return {"message": "Router Users is working!"}

@router.get("") # A rota agora será apenas /users (e não /users/users)
def list_users(
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor)
):
    cursor.execute("SELECT name, email FROM users")
    return cursor.fetchall()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def registrar(user: User, cursor = Depends(get_db_cursor), conn = Depends(get_db_connection)):
    cursor.execute("SELECT email FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = generate_hash(user.password)

    cursor.execute(
        "INSERT INTO users (name, email, password, user_type, create_date) VALUES (%s, %s, %s, %s, NOW())",
        (user.name, user.email, hashed_password, user.user_type)
    )
    conn.commit()

    return {"message": "User created!"}

@router.post("/login")
def login(userLogin: UserLogin, cursor = Depends(get_db_cursor)):
    cursor.execute("SELECT * FROM users WHERE email = %s", (userLogin.email,))
    user_data = cursor.fetchone()

    if not user_data or not verify_password(userLogin.password, user_data['password']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid e-mail or password")

    expires_delta = timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES)
    token = create_token(data={"sub": user_data['email']}, expires_delta=expires_delta)

    return {"message": "Usuário logado com sucesso!", "token": token, "token_type": "bearer"}

@router.patch("/{email}") # PATCH é o correto conceitualmente para atualizações parciais
def update_user(
    email: str, 
    user_update: UserUpdate, 
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    # Extrai apenas os campos que foram de fato enviados na requisição (exclui os Nones)
    update_data = user_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    if "password" in update_data:
        update_data["password"] = generate_hash(update_data["password"])

    # Montagem dinâmica da query SQL (Prevenindo injeção SQL nativamente)
    set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
    values = list(update_data.values())
    values.append(email) # Para o WHERE

    query = f"UPDATE users SET {set_clause} WHERE email = %s"
    
    cursor.execute(query, tuple(values))
    conn.commit()

    return {"message": "User updated successfully!"}

@router.delete("/{email}")
def delete_user(
    email: str, 
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("DELETE FROM users WHERE email = %s", (email,))
    conn.commit()

    return {"message": "User deleted!"}