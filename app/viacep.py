from fastapi import HTTPException
import requests
def search_cep(cep: str):
    url = (f'https://viacep.com.br/ws/{cep}/json/')
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=400, detail='CEP not found')