from fastapi import APIRouter, HTTPException, Depends, status
from app.models import User, UserUpdate
from app.auth import get_current_user
from app.database import get_db_cursor, get_db_connection

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/test")
def test():
    return {"message": "Router Users is working!"}


@router.get("")
def list_users(
    cargo: str = None,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor)
):
    if cargo:
        cursor.execute("SELECT id, nome, email, cargo FROM users WHERE cargo = %s", (cargo,))
    else:
        cursor.execute("SELECT id, nome, email, cargo FROM users")
    return cursor.fetchall()


def _check_self_or_admin(current_user: dict, target_email: str):
    """Permite apenas o próprio usuário ou um admin acessar/modificar."""
    if current_user.get("cargo") != "admin" and current_user.get("email") != target_email:
        raise HTTPException(status_code=403, detail="Sem permissão para modificar este usuário")


@router.patch("/{email}")
def update_user(
    email: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    _check_self_or_admin(current_user, email)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = user_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum dado fornecido para atualizar")

    # Apenas admin pode alterar o cargo
    if "user_type" in update_data and current_user.get("cargo") != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem alterar cargos")

    # Mapeamento: chave Pydantic → coluna no banco
    key_mapping = {
        "name": "nome",
        "user_type": "cargo",
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

    cursor.execute(f"UPDATE users SET {set_clause} WHERE email = %s", tuple(values))
    conn.commit()

    return {"message": "Usuário atualizado com sucesso!"}


@router.delete("/{email}")
def delete_user(
    email: str,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    _check_self_or_admin(current_user, email)

    cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    cursor.execute("DELETE FROM users WHERE email = %s", (email,))
    conn.commit()

    return {"message": "Usuário deletado com sucesso!"}