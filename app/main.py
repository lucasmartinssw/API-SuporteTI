from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .routers import calculadora, usuarios, viacep

app = FastAPI(title="API Calculadora", description="API para realizar operações matemáticas", version="1.0")

@app.get("/")
def root():
    return {"message": "API Calculadora - Bem-vindo!"}

app.include_router(calculadora.router)
app.include_router(usuarios.router)
app.include_router(viacep.router)