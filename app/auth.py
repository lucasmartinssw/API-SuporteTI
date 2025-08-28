from .database import users
from passlib.context import CryptContext

pwd_context = CryptContext(schemes =["bcrypt"], deprecated="auto")
def get_user(username: str):
    return users.find_one({"username": username})

def generate_hash(password: str):
    return pwd_context.hash(password)