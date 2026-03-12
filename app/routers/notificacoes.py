from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.database import get_db_cursor, get_db_connection

router = APIRouter(prefix="/notificacoes", tags=["Notificacoes"])


def create_notificacao(user_id: int, tipo: str, chamado_id: int, mensagem: str, cursor, conn):
    """Helper to insert a notification — called from other routers."""
    try:
        cursor.execute(
            "INSERT INTO notificacoes (user_id, tipo, chamado_id, mensagem) VALUES (%s, %s, %s, %s)",
            (user_id, tipo, chamado_id, mensagem)
        )
        conn.commit()
    except Exception as e:
        print(f"Error creating notificacao: {e}")


@router.get("")
def list_notificacoes(
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor)
):
    """Return all unread notifications for the current user."""
    cursor.execute(
        "SELECT n.*, c.titulo AS chamado_titulo "
        "FROM notificacoes n "
        "JOIN chamados c ON c.id = n.chamado_id "
        "WHERE n.user_id = %s AND n.lida = FALSE "
        "ORDER BY n.created_at DESC "
        "LIMIT 50",
        (current_user.get('id'),)
    )
    return cursor.fetchall()


@router.patch("/lida-todas")
def mark_all_read(
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Dismiss all notifications for the current user."""
    cursor.execute(
        "UPDATE notificacoes SET lida = TRUE WHERE user_id = %s",
        (current_user.get('id'),)
    )
    conn.commit()
    return {"message": "Todas notificações dispensadas"}


@router.patch("/{notificacao_id}/lida")
def mark_one_read(
    notificacao_id: int,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Dismiss a single notification."""
    cursor.execute(
        "UPDATE notificacoes SET lida = TRUE WHERE id = %s AND user_id = %s",
        (notificacao_id, current_user.get('id'))
    )
    conn.commit()
    return {"message": "Notificação dispensada"}