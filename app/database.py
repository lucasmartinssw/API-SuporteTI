import mysql.connector
from fastapi import Depends, HTTPException, status
from app.config import HOST, USER, PASSWORD, DATABASE

def get_db_connection():
    """
    Cria uma nova conexão para cada requisição.
    O 'yield' pausa a função, entrega a conexão para a rota usar,
    e o 'finally' garante que ela seja fechada mesmo se der erro na rota.
    """
    # HOST pode incluir porta (ex: "127.0.0.1:3306") — separar se necessário
    host_parts = HOST.split(":")
    host = host_parts[0]
    port = int(host_parts[1]) if len(host_parts) > 1 else 3306

    conn = None
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        # Entrega a conexão para a requisição atual
        yield conn
        
    except mysql.connector.Error as err:
        print(f"Erro de Banco de Dados: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erro ao conectar com o banco de dados."
        )
        
    finally:
        # Após a requisição terminar (com sucesso ou erro), fecha a conexão
        if conn and conn.is_connected():
            conn.close()


def get_db_cursor(conn = Depends(get_db_connection)):
    """
    Usa a conexão gerada acima para criar um cursor.
    O FastAPI é inteligente o suficiente para compartilhar a mesma conexão
    se a rota pedir o cursor e a conexão ao mesmo tempo.
    """
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
    finally:
        cursor.close()