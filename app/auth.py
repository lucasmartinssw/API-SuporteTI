from .database import users
from passlib.context import CryptContext
from datetime import timedelta, datetime
from .config import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from fastapi import HTTPException

pwd_context = CryptContext(schemes =["bcrypt"], deprecated="auto")
def get_user(username: str):
    return users.find_one({"username": username})

def generate_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user['password']):
        return False
    return user

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
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    usuario = get_user(username)
    if usuario is None:
        raise credentials_exception

    return usuario
