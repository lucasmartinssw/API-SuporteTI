from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.database import get_db_cursor, get_db_connection

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


def log_auditoria(
    tabela: str,
    registro_id: int,
    user_id: int,
    acao: str,
    detalhe: str,
    cursor,
    conn
):
    """Helper — call from other routers to log an audit event."""
    try:
        cursor.execute(
            "INSERT INTO auditoria (tabela, registro_id, usuario_id, acao, descricao) "
            "VALUES (%s, %s, %s, %s, %s)",
            (tabela, registro_id, user_id, acao, detalhe)
        )
        conn.commit()
    except Exception as e:
        print(f"Audit log error: {e}")


@router.get("/chamados/{chamado_id}")
def get_chamado_auditoria(
    chamado_id: int,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
):
    """Return audit log for a chamado. Users can only see their own tickets."""
    user_id = current_user.get("id")
    cargo = current_user.get("cargo")

    # Access check — users can only see their own chamados
    if cargo not in ("admin", "tecnico"):
        cursor.execute(
            "SELECT id FROM chamados WHERE id = %s AND user_id = %s",
            (chamado_id, user_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Sem permissão")

    cursor.execute(
        """
        SELECT a.id, a.acao, a.descricao AS detalhe, a.created_at,
               u.nome AS user_nome, u.email AS user_email, u.cargo AS user_cargo
        FROM auditoria a
        JOIN users u ON a.usuario_id = u.id
        WHERE a.tabela = 'chamados' AND a.registro_id = %s
        ORDER BY a.created_at ASC
        """,
        (chamado_id,)
    )
    return cursor.fetchall()


@router.get("/ativos/{ativo_id}")
def get_ativo_auditoria(
    ativo_id: int,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
):
    """Return audit log for an ativo. IT staff only."""
    if current_user.get("cargo") not in ("admin", "tecnico"):
        raise HTTPException(status_code=403, detail="Sem permissão")

    cursor.execute(
        """
        SELECT a.id, a.acao, a.descricao AS detalhe, a.created_at,
               u.nome AS user_nome, u.email AS user_email, u.cargo AS user_cargo
        FROM auditoria a
        JOIN users u ON a.usuario_id = u.id
        WHERE a.tabela = 'ativos' AND a.registro_id = %s
        ORDER BY a.created_at ASC
        """,
        (ativo_id,)
    )
    return cursor.fetchall()