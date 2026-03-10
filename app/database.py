import mysql.connector
from fastapi import Depends, HTTPException, status

def get_db_connection():
    """
    Cria uma nova conexão para cada requisição.
    O 'yield' pausa a função, entrega a conexão para a rota usar, 
    e o 'finally' garante que ela seja fechada mesmo se der erro na rota.
    """
    conn = None
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="User-12910",
            database="projetofinal"  # use the correct database name
        )
        # ensure_called_table has mensagem_id column
        try:
            temp_cursor = conn.cursor()
            temp_cursor.execute("SHOW COLUMNS FROM chamados_midia LIKE 'mensagem_id'")
            if not temp_cursor.fetchone():
                temp_cursor.execute("ALTER TABLE chamados_midia ADD COLUMN mensagem_id INT NULL")
                temp_cursor.execute(
                    "ALTER TABLE chamados_midia ADD CONSTRAINT fk_mensagem FOREIGN KEY (mensagem_id) REFERENCES chamados_mensagens(id) ON DELETE CASCADE"
                )
                conn.commit()
            temp_cursor.close()
        except Exception:
            # ignore if table doesn't exist yet
            pass
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