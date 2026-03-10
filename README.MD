# Projeto Final RPV - Python FastAPI

## Como usar

1. **Clone o repositório**
   ```sh
   git clone https://github.com/lucasmartinssw/API-SuporteTI
    ```
2. **Instale as dependências**
```sh
pip install -r "requirements.txt"
```

3. **Rode o projeto**
```sh
python -m uvicorn app.main:app --reload
```
**User test**
{
  "name": "Teste Usuario",
  "email": "usuario@teste.com",
  "password": "123456",
  "user_type": "usuario"
}
**admin test**
{
  "name": "Teste Admin",
  "email": "admin@teste.com",
  "password": "123456",
  "user_type": "tecnico"
}