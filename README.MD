# Projeto Final RPV - Python FastAPI

## Como usar

1. **Clone o repositório**
   ```sh
   git clone https://github.com/lucasmartinssw/API-SuporteTI
   ```

2. **Instale as dependências**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure o banco de dados**
   - Abra o MySQL Workbench
   - Execute o arquivo `setup.sql` (File → Open SQL Script → Run All)

4. **Configure o .env**
   ```sh
   copy .env.example .env
   ```
   Edite o `.env` e preencha:
   - `PASSWORD` → sua senha do MySQL
   - `SECRET_KEY` → qualquer string, mas deve ser **igual em todos os computadores**
   - `SUPABASE_URL` → URL do projeto Supabase
   - `SUPABASE_SERVICE_ROLE_KEY` → chave de servidor (necessária para upload no Storage pelo backend)
   - `SUPABASE_BUCKET` → nome do bucket (ex.: `chamados-file`)

5. **Rode o projeto**
   ```sh
   python -m uvicorn app.main:app --reload
   ```

---

## Usuários de teste

Registre via `POST /auth/register` no Swagger (http://127.0.0.1:8000/docs):

**Usuário comum**
```json
{
  "name": "Teste Usuario",
  "email": "usuario@teste.com",
  "password": "123456",
  "user_type": "usuario"
}
```

**Analista TI (admin)**
```json
{
  "name": "Teste Admin",
  "email": "admin@teste.com",
  "password": "123456",
  "user_type": "tecnico"
}
```
