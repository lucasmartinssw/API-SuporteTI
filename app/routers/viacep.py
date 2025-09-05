from fastapi import FastAPI, HTTPException, APIRouter, Depends
from ..viacep import search_cep
from ..auth import get_current_user

router = APIRouter(prefix="/viacep", tags=["Via CEP"])

@router.get("/")
def test():
    return {"message": "Rota Via CEP funcionando!"}

@router.get("/{cep}")
def get_cep(cep: str, usuario = Depends(get_current_user)):
    return search_cep(cep)