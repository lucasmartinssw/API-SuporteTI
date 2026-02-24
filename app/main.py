from fastapi import FastAPI
from .routers import usuarios, auth, chamados

app = FastAPI(title="API Final Project", description="API for Final Project", version="1.0")


@app.get("/")
def root():
    return {"message": "API Final Project - Bem-vindo!"}


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(chamados.router)