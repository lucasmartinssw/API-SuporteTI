import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from ..models import ChamadoCreate, ChamadoOut, MensagemCreate
from ..auth import get_current_user
from ..database import get_db_cursor, get_db_connection

router = APIRouter(prefix="/chamados", tags=["Chamados"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("")
def list_chamados(current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor)):
    user_id = current_user.get('id')
    user_cargo = current_user.get('cargo')

    if user_cargo in ('admin', 'tecnico'):
        cursor.execute("SELECT * FROM chamados")
    else:
        cursor.execute("SELECT * FROM chamados WHERE user_id = %s", (user_id,))

    return cursor.fetchall()


@router.post("/json", status_code=status.HTTP_201_CREATED)
def create_chamado_json(
    chamado: ChamadoCreate,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Create chamado with JSON body (no files)."""
    user_id = current_user.get('id')

    try:
        cursor.execute(
            "INSERT INTO chamados (titulo, descricao, user_id, status_id, prioridade_id, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
            (chamado.title, chamado.description, user_id, 1, 2)
        )
        conn.commit()

        chamado_id = None
        try:
            chamado_id = cursor.lastrowid
        except Exception:
            chamado_id = None

        # Fallback: find the inserted row by titulo/user_id if lastrowid not available
        if not chamado_id:
            cursor.execute(
                "SELECT id FROM chamados WHERE titulo = %s AND user_id = %s ORDER BY created_at DESC LIMIT 1",
                (chamado.title, user_id)
            )
            row = cursor.fetchone()
            chamado_id = row['id'] if row else None

        return {"message": "Chamado criado", "id": chamado_id}
    except Exception as e:
        import traceback
        import sys
        print("Error creating chamado:")
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(status_code=500, detail=f"Internal server error creating chamado: {str(e)}")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_chamado(
    chamado: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    # `chamado` is received as a JSON string in multipart/form-data. Parse to model.
    import json
    try:
        chamado_data = json.loads(chamado)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid JSON in 'chamado' form field")

    # Validate/construct Pydantic model
    try:
        chamado_obj = ChamadoCreate(**chamado_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    user_id = current_user.get('id')

    import traceback
    try:
        cursor.execute(
            "INSERT INTO chamados (titulo, descricao, user_id, status_id, prioridade_id, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
            (chamado_obj.title, chamado_obj.description, user_id, 1, 2)
        )
        conn.commit()

        chamado_id = None
        try:
            chamado_id = cursor.lastrowid
        except Exception:
            chamado_id = None

        # Fallback: find the inserted row by titulo/user_id if lastrowid not available
        if not chamado_id:
            cursor.execute(
                "SELECT id FROM chamados WHERE titulo = %s AND user_id = %s ORDER BY created_at DESC LIMIT 1",
                (chamado_obj.title, user_id)
            )
            row = cursor.fetchone()
            chamado_id = row['id'] if row else None

        # Save attachments
        if files:
            for upload in files:
                # ensure UploadFile type
                try:
                    filename = f"{chamado_id}_{upload.filename}" if chamado_id else upload.filename
                    path = os.path.join(UPLOAD_DIR, filename)
                    with open(path, "wb") as f:
                        f.write(upload.file.read())
                    cursor.execute(
                        "INSERT INTO chamados_midia (chamado_id, url_arquivo, tipo_arquivo) VALUES (%s, %s, %s)",
                        (chamado_id, path, upload.content_type)
                    )
                except Exception as e:
                    # rollback file-related DB inserts if something fails
                    print("Error saving uploaded file:", e)
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=f"Error saving attachment: {str(e)}")
            conn.commit()

        return {"message": "Chamado criado", "id": chamado_id}
    except Exception as e:
        # Print traceback to server logs for debugging; return 500 with safe message
        import sys
        print("Error creating chamado:")
        traceback.print_exc(file=sys.stdout)
        raise HTTPException(status_code=500, detail=f"Internal server error creating chamado: {str(e)}")


@router.get("/{chamado_id}")
def get_chamado(chamado_id: int, current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor)):
    cursor.execute("SELECT * FROM chamados WHERE id = %s", (chamado_id,))
    chamado = cursor.fetchone()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado not found")

    # Attachments
    cursor.execute("SELECT id, url_arquivo, tipo_arquivo FROM chamados_midia WHERE chamado_id = %s", (chamado_id,))
    arquivos = cursor.fetchall()
    chamado['midia'] = arquivos
    return chamado


@router.patch("/{chamado_id}")
def update_chamado(chamado_id: int, data: dict, current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor), conn = Depends(get_db_connection)):
    user_cargo = current_user.get('cargo')
    if user_cargo not in ('admin', 'tecnico'):
        raise HTTPException(status_code=403, detail="Only technicians or admins can update chamados")

    # Allow only status_id and prioridade_id updates
    allowed = {k: v for k, v in data.items() if k in ('status_id', 'prioridade_id')}
    if not allowed:
        raise HTTPException(status_code=400, detail="No updatable fields provided")

    set_clause = ", ".join([f"{k} = %s" for k in allowed.keys()])
    values = list(allowed.values())
    values.append(chamado_id)
    query = f"UPDATE chamados SET {set_clause}, updated_at = NOW() WHERE id = %s"
    cursor.execute(query, tuple(values))
    conn.commit()
    return {"message": "Chamado updated"}


@router.get("/{chamado_id}/mensagens")
def list_mensagens(chamado_id: int, current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor)):
    # Verify chamado exists
    cursor.execute("SELECT id FROM chamados WHERE id = %s", (chamado_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Chamado {chamado_id} not found")
    
    cursor.execute("SELECT id, chamado_id, user_id, mensagem, enviado_em FROM chamados_mensagens WHERE chamado_id = %s ORDER BY enviado_em", (chamado_id,))
    return cursor.fetchall()


@router.post("/{chamado_id}/mensagens", status_code=status.HTTP_201_CREATED)
def post_mensagem(chamado_id: int, mensagem: MensagemCreate, current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor), conn = Depends(get_db_connection)):
    # Verify chamado exists
    cursor.execute("SELECT id FROM chamados WHERE id = %s", (chamado_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Chamado {chamado_id} not found")
    
    user_id = current_user.get('id')
    cursor.execute(
        "INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em) VALUES (%s, %s, %s, NOW())",
        (chamado_id, user_id, mensagem.content)
    )
    conn.commit()
    return {"message": "Mensagem enviada"}
