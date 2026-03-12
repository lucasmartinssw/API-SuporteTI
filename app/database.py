import mysql.connector
from fastapi import Depends, HTTPException, status
from app.config import HOST, USER, PASSWORD, DATABASE

_schema_checked = False


def _ensure_schema(conn):
    """Verifica e atualiza o schema do banco uma única vez por instância."""
    global _schema_checked
    if _schema_checked:
        return
    try:
        cur = conn.cursor()
        cur.execute("SHOW COLUMNS FROM chamados_midia LIKE 'mensagem_id'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE chamados_midia ADD COLUMN mensagem_id INT NULL")
            cur.execute(
                "ALTER TABLE chamados_midia ADD CONSTRAINT fk_mensagem "
                "FOREIGN KEY (mensagem_id) REFERENCES chamados_mensagens(id) ON DELETE CASCADE"
            )
            conn.commit()
        cur.close()
        _schema_checked = True
    except Exception:
        pass


def get_db_connection():
    """
    Cria uma nova conexão para cada requisição.
    O 'yield' pausa a função, entrega a conexão para a rota usar,
    e o 'finally' garante que ela seja fechada mesmo se der erro na rota.
    """
    conn = None
    try:
        db_host = HOST.split(":")[0] if ":" in HOST else HOST
        db_port = int(HOST.split(":")[1]) if ":" in HOST else 3306

        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        _ensure_schema(conn)
        yield conn

    except mysql.connector.Error as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao conectar com o banco de dados."
        )

    finally:
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