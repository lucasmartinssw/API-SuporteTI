from fastapi import FastAPI
from .routers import usuarios, auth, chamados
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Final Project", description="API for Final Project", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, coloque a URL do seu front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API Final Project - Bem-vindo!"}


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(chamados.router) 