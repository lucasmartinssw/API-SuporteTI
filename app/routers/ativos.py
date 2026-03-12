from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth import get_current_user
from app.routers.auditoria import log_auditoria
from app.database import get_db_cursor, get_db_connection

router = APIRouter(prefix="/ativos", tags=["Ativos"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class AtivoCreate(BaseModel):
    nome: str
    tipo: str
    numero_serie: Optional[str] = None
    patrimonio: Optional[str] = None
    localizacao: Optional[str] = None
    status: Optional[str] = "ativo"
    responsavel_id: Optional[int] = None
    observacoes: Optional[str] = None

class AtivoUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    numero_serie: Optional[str] = None
    patrimonio: Optional[str] = None
    localizacao: Optional[str] = None
    status: Optional[str] = None
    responsavel_id: Optional[int] = None
    observacoes: Optional[str] = None


# ── helpers ───────────────────────────────────────────────────────────────────

def _require_tech(current_user: dict):
    if current_user.get("cargo") not in ("admin", "tecnico"):
        raise HTTPException(status_code=403, detail="Apenas técnicos ou admins podem gerenciar ativos.")


# ── LIST ──────────────────────────────────────────────────────────────────────

@router.get("")
def list_ativos(
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    localizacao: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
):
    base_query = """
        SELECT a.*, u.nome AS responsavel_nome, u.email AS responsavel_email
        FROM ativos a
        LEFT JOIN users u ON a.responsavel_id = u.id
        WHERE 1=1
    """
    params: list = []

    cargo = current_user.get("cargo")
    # Regular users only see active assets; techs/admins see all unless filtered
    if cargo not in ("admin", "tecnico"):
        base_query += " AND a.status = 'ativo'"

    if tipo:
        base_query += " AND a.tipo = %s"
        params.append(tipo)
    if status:
        base_query += " AND a.status = %s"
        params.append(status)
    if localizacao:
        base_query += " AND a.localizacao LIKE %s"
        params.append(f"%{localizacao}%")

    base_query += " ORDER BY a.created_at DESC"
    cursor.execute(base_query, tuple(params))
    ativos = cursor.fetchall()

    # Attach chamados count to each ativo
    for ativo in ativos:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM chamados_ativos WHERE ativo_id = %s",
            (ativo["id"],)
        )
        row = cursor.fetchone()
        ativo["chamados_count"] = row["total"] if row else 0

    return ativos


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_ativo(
    data: AtivoCreate,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
    conn=Depends(get_db_connection),
):
    _require_tech(current_user)

    valid_tipos = ("computador", "monitor", "impressora", "telefone", "servidor", "switch", "outro")
    if data.tipo not in valid_tipos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Valores aceitos: {valid_tipos}")

    cursor.execute(
        """
        INSERT INTO ativos
            (nome, tipo, numero_serie, patrimonio, localizacao, status, responsavel_id, observacoes, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """,
        (
            data.nome,
            data.tipo,
            data.numero_serie,
            data.patrimonio,
            data.localizacao,
            data.status or "ativo",
            data.responsavel_id,
            data.observacoes,
        ),
    )
    conn.commit()
    ativo_id = cursor.lastrowid
    actor = current_user.get('nome') or current_user.get('email', '')
    log_auditoria('ativos', ativo_id, current_user['id'], 'criado',
        f"Ativo '{data.nome}' criado por {actor}", cursor, conn)
    return {"message": "Ativo criado com sucesso.", "id": ativo_id}


# ── GET ONE ───────────────────────────────────────────────────────────────────

@router.get("/{ativo_id}")
def get_ativo(
    ativo_id: int,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
):
    cursor.execute(
        """
        SELECT a.*, u.nome AS responsavel_nome, u.email AS responsavel_email
        FROM ativos a
        LEFT JOIN users u ON a.responsavel_id = u.id
        WHERE a.id = %s
        """,
        (ativo_id,),
    )
    ativo = cursor.fetchone()
    if not ativo:
        raise HTTPException(status_code=404, detail="Ativo não encontrado.")

    cursor.execute(
        """
        SELECT c.id, c.titulo, c.descricao, c.created_at, c.updated_at,
               sc.nome AS status, p.nivel AS prioridade,
               u.nome AS solicitante
        FROM chamados_ativos ca
        JOIN chamados c ON ca.chamado_id = c.id
        LEFT JOIN status_chamado sc ON c.status_id = sc.id
        LEFT JOIN prioridades p ON c.prioridade_id = p.id
        LEFT JOIN users u ON c.user_id = u.id
        WHERE ca.ativo_id = %s
        ORDER BY c.created_at DESC
        """,
        (ativo_id,),
    )
    ativo["chamados"] = cursor.fetchall()
    return ativo


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.patch("/{ativo_id}")
def update_ativo(
    ativo_id: int,
    data: AtivoUpdate,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
    conn=Depends(get_db_connection),
):
    _require_tech(current_user)

    cursor.execute("SELECT id FROM ativos WHERE id = %s", (ativo_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Ativo não encontrado.")

    allowed = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
    if not allowed:
        raise HTTPException(status_code=400, detail="Nenhum campo válido para atualizar.")

    set_clause = ", ".join(f"{k} = %s" for k in allowed)
    values = list(allowed.values()) + [ativo_id]
    cursor.execute(f"UPDATE ativos SET {set_clause}, updated_at = NOW() WHERE id = %s", tuple(values))
    conn.commit()
    actor = current_user.get('nome') or current_user.get('email', '')
    changes = ", ".join(f"{k}={v}" for k, v in allowed.items())
    if 'status' in allowed and allowed['status'] == 'desativado':
        log_auditoria('ativos', ativo_id, current_user['id'], 'desativado',
            f"Ativo desativado por {actor}", cursor, conn)
    else:
        log_auditoria('ativos', ativo_id, current_user['id'], 'campo_alterado',
            f"Campos alterados por {actor}: {changes}", cursor, conn)
    return {"message": "Ativo atualizado com sucesso."}


# ── DELETE (soft) ─────────────────────────────────────────────────────────────

@router.delete("/{ativo_id}")
def deactivate_ativo(
    ativo_id: int,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
    conn=Depends(get_db_connection),
):
    _require_tech(current_user)

    cursor.execute("SELECT id FROM ativos WHERE id = %s", (ativo_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Ativo não encontrado.")

    cursor.execute("UPDATE ativos SET status = 'desativado', updated_at = NOW() WHERE id = %s", (ativo_id,))
    conn.commit()
    return {"message": "Ativo desativado com sucesso."}


# ── LINK / UNLINK chamado ─────────────────────────────────────────────────────

@router.post("/{ativo_id}/chamados/{chamado_id}", status_code=status.HTTP_201_CREATED)
def link_chamado(
    ativo_id: int,
    chamado_id: int,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
    conn=Depends(get_db_connection),
):
    _require_tech(current_user)

    cursor.execute("SELECT id FROM ativos WHERE id = %s", (ativo_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Ativo não encontrado.")
    cursor.execute("SELECT id FROM chamados WHERE id = %s", (chamado_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")

    try:
        cursor.execute(
            "INSERT INTO chamados_ativos (chamado_id, ativo_id) VALUES (%s, %s)",
            (chamado_id, ativo_id),
        )
        conn.commit()
    except Exception:
        raise HTTPException(status_code=409, detail="Vínculo já existe.")
    actor = current_user.get('nome') or current_user.get('email', '')
    log_auditoria('ativos', ativo_id, current_user['id'], 'ativo_vinculado',
        f"Chamado #{chamado_id} vinculado por {actor}", cursor, conn)
    log_auditoria('chamados', chamado_id, current_user['id'], 'ativo_vinculado',
        f"Ativo #{ativo_id} vinculado por {actor}", cursor, conn)
    return {"message": "Chamado vinculado ao ativo."}


@router.delete("/{ativo_id}/chamados/{chamado_id}")
def unlink_chamado(
    ativo_id: int,
    chamado_id: int,
    current_user: dict = Depends(get_current_user),
    cursor=Depends(get_db_cursor),
    conn=Depends(get_db_connection),
):
    _require_tech(current_user)
    cursor.execute(
        "DELETE FROM chamados_ativos WHERE chamado_id = %s AND ativo_id = %s",
        (chamado_id, ativo_id),
    )
    conn.commit()
    actor = current_user.get('nome') or current_user.get('email', '')
    log_auditoria('ativos', ativo_id, current_user['id'], 'ativo_desvinculado',
        f"Chamado #{chamado_id} desvinculado por {actor}", cursor, conn)
    log_auditoria('chamados', chamado_id, current_user['id'], 'ativo_desvinculado',
        f"Ativo #{ativo_id} desvinculado por {actor}", cursor, conn)
    return {"message": "Vínculo removido."}