from pymongo import MongoClient
from .config import MONGO_URL, MONGO_DB

client = MongoClient(MONGO_URL)
db = client[MONGO_DB]
users = db["users"]
