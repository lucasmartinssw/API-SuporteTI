from fastapi import APIRouter, HTTPException, Depends, status
from ..models import User, UserUpdate
from ..auth import get_current_user
from ..database import get_db_cursor, get_db_connection

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/test")
def test():
    return {"message": "Router Users is working!"}


@router.get("")
def list_users(
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor)
):
    cursor.execute("SELECT id, nome, email, cargo FROM users")
    return cursor.fetchall()


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

    if "password" in update_data:
        # hash responsibility remains in auth utilities; import to use if needed elsewhere
        from ..auth import generate_hash
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