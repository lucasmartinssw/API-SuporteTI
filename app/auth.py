from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import mysql.connector

from app.config import SECRET_KEY, ALGORITHM, HOST, USER, PASSWORD, DATABASE

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def generate_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Parse host and port from HOST config (format: "127.0.0.1:3306")
        host_parts = HOST.split(":")
        db_host = host_parts[0]
        db_port = int(host_parts[1]) if len(host_parts) > 1 else 3306

        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nome, email, cargo FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")