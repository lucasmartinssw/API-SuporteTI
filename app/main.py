from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .routers import usuarios

app = FastAPI(title="API Final Project", description="API for Final Project", version="1.0")

@app.get("/")
def root():
    return {"message": "API Final Project - Bem-vindo!"}

app.include_router(usuarios.router)