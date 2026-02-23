import bcrypt
import hashlib
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import SECRET_KEY, ALGORITHM
from .database import get_db_cursor 

# 1. Trocamos o OAuth2PasswordBearer pelo HTTPBearer
security = HTTPBearer()

def get_user_by_email(email: str, cursor):
    """Busca o usuário no banco pelo email."""
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    return cursor.fetchone()

def pre_processar_senha(password: str) -> str:
    """Garante que qualquer senha vire um hash de 64 caracteres antes do Bcrypt."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_hash(password: str) -> str:
    senha_segura = pre_processar_senha(password)
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(senha_segura.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    senha_segura = pre_processar_senha(plain_password)
    try:
        return bcrypt.checkpw(
            senha_segura.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except (ValueError, TypeError):
        return False

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 2. Atualizamos a dependência para receber o HTTPAuthorizationCredentials
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    cursor = Depends(get_db_cursor)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        # 3. Extraímos o token de dentro do objeto credentials
        token = credentials.credentials
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(email=email, cursor=cursor)
    
    if user is None:
        raise credentials_exception

    return user