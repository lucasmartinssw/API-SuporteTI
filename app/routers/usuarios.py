from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from typing import List, Optional
from app.models import User, UserUpdate
from app.auth import get_current_user
from app.database import get_db_cursor, get_db_connection
from app.supabase_storage import upload_file_to_supabase

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/test")
def test():
    return {"message": "Router Users is working!"}


@router.get("")
def list_users(
    cargo: str = None,
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor)
):
    is_it = current_user.get("cargo") in ("admin", "tecnico")
    # Only IT staff can see inactive users, and only when explicitly requested
    show_inactive = is_it and include_inactive
    base = "SELECT id, nome, email, cargo, avatar_url, COALESCE(ativo, 1) as ativo FROM users"
    if cargo and not show_inactive:
        cursor.execute(base + " WHERE cargo = %s AND COALESCE(ativo, 1) = 1", (cargo,))
    elif cargo:
        cursor.execute(base + " WHERE cargo = %s", (cargo,))
    elif show_inactive:
        cursor.execute(base)
    else:
        cursor.execute(base + " WHERE COALESCE(ativo, 1) = 1")
    return cursor.fetchall()


# ── Profile endpoints ─────────────────────────────────────────

@router.get("/me")
def get_my_profile(
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor)
):
    """Return full profile for the logged-in user."""
    user_id = current_user.get("id")

    # Base user info
    cursor.execute(
        "SELECT id, nome, email, cargo, bio, avatar_url FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Their chamados — as creator OR as assigned tecnico
    cursor.execute(
        "SELECT DISTINCT c.id, c.titulo, c.created_at, c.updated_at, "
        "s.nome AS status, p.nivel AS prioridade "
        "FROM chamados c "
        "LEFT JOIN status_chamado s ON s.id = c.status_id "
        "LEFT JOIN prioridades p ON p.id = c.prioridade_id "
        "LEFT JOIN chamados_tecnicos ct ON ct.chamado_id = c.id "
        "WHERE c.user_id = %s OR ct.user_id = %s "
        "ORDER BY c.created_at DESC",
        (user_id, user_id)
    )
    chamados = cursor.fetchall()

    # Their comments/messages
    cursor.execute(
        "SELECT m.id, m.mensagem, m.enviado_em, m.chamado_id, c.titulo AS chamado_titulo "
        "FROM chamados_mensagens m "
        "JOIN chamados c ON c.id = m.chamado_id "
        "WHERE m.user_id = %s "
        "ORDER BY m.enviado_em DESC "
        "LIMIT 50",
        (user_id,)
    )
    comentarios = cursor.fetchall()

    # Ativos linked to chamados the user created or is assigned to as tecnico
    cursor.execute(
        "SELECT DISTINCT a.id, a.nome, a.tipo, a.numero_serie, a.patrimonio, a.localizacao, a.status "
        "FROM ativos a "
        "JOIN chamados_ativos ca ON ca.ativo_id = a.id "
        "JOIN chamados c ON c.id = ca.chamado_id "
        "LEFT JOIN chamados_tecnicos ct ON ct.chamado_id = c.id "
        "WHERE c.user_id = %s OR ct.user_id = %s "
        "ORDER BY a.nome",
        (user_id, user_id)
    )
    ativos = cursor.fetchall()

    return {
        **user,
        "chamados": chamados,
        "comentarios": comentarios,
        "ativos": ativos,
    }


@router.patch("/me")
def update_my_profile(
    data: dict,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Update name and/or bio for the logged-in user."""
    user_id = current_user.get("id")

    allowed = {}
    if "nome" in data and data["nome"]:
        allowed["nome"] = str(data["nome"])[:100]
    if "bio" in data:
        allowed["bio"] = str(data["bio"])[:500] if data["bio"] else None

    if not allowed:
        raise HTTPException(status_code=400, detail="Nenhum campo válido para atualizar")

    set_clause = ", ".join([f"{k} = %s" for k in allowed.keys()])
    values = list(allowed.values())
    values.append(user_id)
    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", tuple(values))
    conn.commit()

    return {"message": "Perfil atualizado com sucesso"}


@router.post("/me/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Upload a profile picture to Supabase and save the URL."""
    user_id = current_user.get("id")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Apenas imagens são permitidas")

    try:
        # Reuse upload_file_to_supabase — pass user_id as chamado_id with a dedicated folder
        # We override the path by monkey-patching the filename to get avatars/ prefix
        import uuid
        from datetime import datetime
        from app.config import SUPABASE_URL, SUPABASE_BUCKET
        from app.supabase_storage import _get_supabase_client

        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        file_path = f"avatars/{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
        file_content = file.file.read()

        supabase = _get_supabase_client()
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        avatar_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)

        cursor.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (avatar_url, user_id))
        conn.commit()

        return {"message": "Avatar atualizado", "avatar_url": avatar_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload do avatar: {str(e)}")



@router.get("/{user_id}/profile")
def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor)
):
    """Return public profile for any user (read-only)."""
    cursor.execute(
        "SELECT id, nome, email, cargo, bio, avatar_url FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Chamados as creator or tecnico
    cursor.execute(
        "SELECT DISTINCT c.id, c.titulo, c.created_at, c.updated_at, "
        "s.nome AS status, p.nivel AS prioridade "
        "FROM chamados c "
        "LEFT JOIN status_chamado s ON s.id = c.status_id "
        "LEFT JOIN prioridades p ON p.id = c.prioridade_id "
        "LEFT JOIN chamados_tecnicos ct ON ct.chamado_id = c.id "
        "WHERE c.user_id = %s OR ct.user_id = %s "
        "ORDER BY c.created_at DESC",
        (user_id, user_id)
    )
    chamados = cursor.fetchall()

    cursor.execute(
        "SELECT m.id, m.mensagem, m.enviado_em, m.chamado_id, c.titulo AS chamado_titulo "
        "FROM chamados_mensagens m "
        "JOIN chamados c ON c.id = m.chamado_id "
        "WHERE m.user_id = %s "
        "ORDER BY m.enviado_em DESC "
        "LIMIT 50",
        (user_id,)
    )
    comentarios = cursor.fetchall()

    cursor.execute(
        "SELECT DISTINCT a.id, a.nome, a.tipo, a.numero_serie, a.patrimonio, a.localizacao, a.status "
        "FROM ativos a "
        "JOIN chamados_ativos ca ON ca.ativo_id = a.id "
        "JOIN chamados c ON c.id = ca.chamado_id "
        "LEFT JOIN chamados_tecnicos ct ON ct.chamado_id = c.id "
        "WHERE c.user_id = %s OR ct.user_id = %s "
        "ORDER BY a.nome",
        (user_id, user_id)
    )
    ativos = cursor.fetchall()

    return {**user, "chamados": chamados, "comentarios": comentarios, "ativos": ativos}


@router.delete("/me/avatar")
def remove_avatar(
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection),
):
    """Remove the user's avatar and revert to initials."""
    cursor.execute("UPDATE users SET avatar_url = NULL WHERE id = %s", (current_user["id"],))
    conn.commit()
    return {"message": "Avatar removido com sucesso."}


# ── Admin: update user by ID ──────────────────────────────────

class UserAdminUpdate(BaseModel):
    nome: Optional[str] = None
    cargo: Optional[str] = None

@router.patch("/{user_id}/admin")
def admin_update_user(
    user_id: int,
    data: UserAdminUpdate,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection),
):
    if current_user.get("cargo") not in ("admin", "tecnico"):
        raise HTTPException(status_code=403, detail="Sem permissão.")
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")
    if "cargo" in updates and updates["cargo"] not in ("usuario", "tecnico", "admin"):
        raise HTTPException(status_code=400, detail="Cargo inválido.")
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", (*updates.values(), user_id))
    conn.commit()
    return {"message": "Usuário atualizado."}


# ── Admin: reset password ─────────────────────────────────────

class PasswordReset(BaseModel):
    nova_senha: str

@router.patch("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    data: PasswordReset,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection),
):
    if current_user.get("cargo") not in ("admin", "tecnico"):
        raise HTTPException(status_code=403, detail="Sem permissão.")
    if len(data.nova_senha) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 6 caracteres.")
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    from app.auth import generate_hash
    cursor.execute("UPDATE users SET senha = %s WHERE id = %s", (generate_hash(data.nova_senha), user_id))
    conn.commit()
    return {"message": "Senha redefinida com sucesso."}


# ── Admin: deactivate user ────────────────────────────────────

@router.patch("/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection),
):
    if current_user.get("cargo") not in ("admin", "tecnico"):
        raise HTTPException(status_code=403, detail="Sem permissão.")
    if current_user.get("id") == user_id:
        raise HTTPException(status_code=400, detail="Não é possível desativar sua própria conta.")
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    cursor.execute("UPDATE users SET ativo = 0 WHERE id = %s", (user_id,))
    conn.commit()
    return {"message": "Usuário desativado."}



# ── Existing endpoints (legacy, kept for compatibility) ──────────────

@router.patch("/{email}")
def update_user(
    email: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    key_mapping = {
        "name": "nome",
        "user_type": "cargo"
    }

    for py_key, db_col in key_mapping.items():
        if py_key in update_data:
            update_data[db_col] = update_data.pop(py_key)

    if "password" in update_data:
        from app.auth import generate_hash
        update_data["senha"] = generate_hash(update_data.pop("password"))

    set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
    values = list(update_data.values())
    values.append(email)

    query = f"UPDATE users SET {set_clause} WHERE email = %s"
    cursor.execute(query, tuple(values))
    conn.commit()

    return {"message": "User updated successfully!"}


@router.delete("/{email}")
def delete_user(
    email: str,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("DELETE FROM users WHERE email = %s", (email,))
    conn.commit()

    return {"message": "User deleted!"}