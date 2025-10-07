from datetime import timedelta, datetime
from jose import jwt, JWTError
from fastapi import HTTPException
from passlib.context import CryptContext

from .config import SECRET_KEY, ALGORITHM
from .database import cursor

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(name: str):
    cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
    user = cursor.fetchone()
    return user

def generate_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail='Invalid credentials',
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name: str = payload.get("sub")
        if user_name is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(name=user_name)
    if user is None:
        raise credentials_exception

    return user