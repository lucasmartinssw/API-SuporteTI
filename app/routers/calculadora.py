from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from ..models import OperacaoDoisNumeros
router = APIRouter(prefix="/calc", tags=["Calculadora"])

@router.get("/subtracao")
def subtracao(a: float, b: float):
    return {"resultado": a - b}

@router.get("/soma")
def soma(a: float, b: float):
    return {"resultado": a + b}

@router.post('/soma')
def soma_post(dados: OperacaoDoisNumeros):
    return {"resultado": dados.a + dados.b}

@router.post('/subtracao')
def subtracao(dados: OperacaoDoisNumeros):
    return {"resultado": dados.a - dados.b}

@router.post('/multiplicacao')
def multiplicacao(dados: OperacaoDoisNumeros):
    return {"resultado": dados.a * dados.b}

@router.post('/divisao')
def divisao(dados: OperacaoDoisNumeros):
    if dados.b == 0:
        raise HTTPException(status_code=400, detail="Divisão por zero não é permitida.")
    return {"resultado": dados.a / dados.b}

@router.post("/potencia")
async def potencia(valores: OperacaoDoisNumeros):
    if valores.a is None or valores.b is None:
        raise HTTPException(status_code=400, detail="Valores 'a' e 'b' são obrigatórios")
    return {"resultado": valores.a ** valores.b}

@router.post("/raiz")
async def raiz(valores: OperacaoDoisNumeros):
    if valores.a is None or valores.b is None:
        raise HTTPException(status_code=400, detail="Valores 'a' e 'b' são obrigatórios")
    if valores.a < 0:
        raise HTTPException(status_code=400, detail="Raiz quadrada de número negativo não é permitida")
    return {"resultado": valores.a ** (1 / valores.b)}