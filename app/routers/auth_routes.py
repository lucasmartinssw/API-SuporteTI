from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
from app.models import User, UserLogin
from app.auth import generate_hash, verify_password, create_token
from app.database import get_db_cursor, get_db_connection
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: User, cursor=Depends(get_db_cursor), conn=Depends(get_db_connection)):
    cursor.execute("SELECT email FROM users WHERE email = %s", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    hashed_password = generate_hash(user.password)

    cursor.execute(
        "INSERT INTO users (nome, email, senha, cargo, created_at) VALUES (%s, %s, %s, %s, NOW())",
        (user.name, user.email, hashed_password, user.user_type)
    )
    conn.commit()

    user_id = None
    try:
        user_id = cursor.lastrowid
    except Exception:
        pass

    return {"message": "Usuário criado com sucesso!", "user_id": user_id}


@router.post("/login")
def login(userLogin: UserLogin, cursor=Depends(get_db_cursor)):
    cursor.execute("SELECT * FROM users WHERE email = %s", (userLogin.email,))
    user_data = cursor.fetchone()

    if not user_data or not verify_password(userLogin.password, user_data['senha']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")

    # Block deactivated accounts — same error message to avoid revealing account existence
    if user_data.get('ativo', 1) == 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")

    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_token(data={"sub": user_data['email']}, expires_delta=expires_delta)

    return {
        "message": "Usuário logado com sucesso!",
        "token": token,
        "token_type": "bearer",
        "name": user_data['nome'],
        "user_type": user_data['cargo'],
        "email": user_data['email']
    }