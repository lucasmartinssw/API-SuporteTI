import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from ..models import ChamadoCreate, ChamadoOut, MensagemCreate
from ..auth import get_current_user
from ..database import get_db_cursor, get_db_connection
from ..supabase_storage import upload_file_to_supabase, delete_file_from_supabase
import traceback

router = APIRouter(prefix="/chamados", tags=["Chamados"])


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
    title: str = Form(..., description="Título do chamado"),
    description: str = Form(..., description="Descrição detalhada do problema"),
    files: List[UploadFile] = File(default=[], description="Arquivos anexos (opcional)"),
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Create chamado with optional file attachments using Supabase Storage
    
    Similar to /json endpoint but accepts FormData for multipart uploads.
    Use this for uploading files together with the chamado.
    """
    user_id = current_user.get('id')

    # sanitize files param (Swagger may send empty string or a list containing a string)
    if isinstance(files, str):
        files = []
    elif isinstance(files, list):
        files = [f for f in files if not isinstance(f, str)]

    try:
        # Insert chamado in database
        cursor.execute(
            "INSERT INTO chamados (titulo, descricao, user_id, status_id, prioridade_id, created_at) VALUES (%s, %s, %s, %s, %s, NOW())",
            (title, description, user_id, 1, 2)
        )
        conn.commit()

        # Get chamado ID
        chamado_id = None
        try:
            chamado_id = cursor.lastrowid
        except Exception:
            chamado_id = None

        # Fallback: find the inserted row by titulo/user_id if lastrowid not available
        if not chamado_id:
            cursor.execute(
                "SELECT id FROM chamados WHERE titulo = %s AND user_id = %s ORDER BY created_at DESC LIMIT 1",
                (title, user_id)
            )
            row = cursor.fetchone()
            chamado_id = row['id'] if row else None

        # Upload attachments to Supabase Storage
        if files:
            for upload in files:
                try:
                    # Upload file to Supabase
                    file_info = upload_file_to_supabase(upload, chamado_id)
                    
                    # Save metadata in database
                    cursor.execute(
                        "INSERT INTO chamados_midia (chamado_id, url_arquivo, tipo_arquivo) VALUES (%s, %s, %s)",
                        (chamado_id, file_info['url'], file_info['content_type'])
                    )
                except Exception as e:
                    print("Error uploading file to Supabase:", str(e))
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=f"Error uploading attachment: {str(e)}")
            
            conn.commit()

        return {
            "message": "Chamado criado com sucesso",
            "id": chamado_id,
            "files_uploaded": len(files) if files else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        print("Error creating chamado:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
def post_mensagem(
    chamado_id: int,
    mensagem: str = Form(..., description="Conteúdo da mensagem/resposta"),
    files: Optional[List[UploadFile]] = File(default=None, description="Arquivos anexos (opcional)"),
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Post message with optional file attachments using Supabase Storage"""
    # Verify chamado exists
    cursor.execute("SELECT id FROM chamados WHERE id = %s", (chamado_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Chamado {chamado_id} not found")
    
    user_id = current_user.get('id')
    
    # Tratamento corrigido para lidar com nulos e strings vazias do Swagger
    if files is None:
        files = []
    elif isinstance(files, str):
        files = []
    elif isinstance(files, list):
        files = [f for f in files if not isinstance(f, str)]
    
    try:
        # Insert message in database
        cursor.execute(
            "INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em) VALUES (%s, %s, %s, NOW())",
            (chamado_id, user_id, mensagem)
        )
        conn.commit()

        # Get mensagem ID
        mensagem_id = None
        try:
            mensagem_id = cursor.lastrowid
        except Exception:
            mensagem_id = None

        # Fallback: find the inserted row if lastrowid not available
        if not mensagem_id:
            cursor.execute(
                "SELECT id FROM chamados_mensagens WHERE chamado_id = %s AND user_id = %s ORDER BY enviado_em DESC LIMIT 1",
                (chamado_id, user_id)
            )
            row = cursor.fetchone()
            mensagem_id = row['id'] if row else None

        # Upload attachments to Supabase Storage if provided
        if files:
            for upload in files:
                try:
                    # Upload file to Supabase
                    file_info = upload_file_to_supabase(upload, chamado_id, mensagem_id)
                    
                    # Save metadata in database
                    cursor.execute(
                        "INSERT INTO chamados_midia (chamado_id, mensagem_id, url_arquivo, tipo_arquivo) VALUES (%s, %s, %s, %s)",
                        (chamado_id, mensagem_id, file_info['url'], file_info['content_type'])
                    )
                except Exception as e:
                    print("Error uploading file to Supabase:", str(e))
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=f"Error uploading attachment: {str(e)}")
            
            conn.commit()

        return {
            "message": "Mensagem enviada com sucesso",
            "mensagem_id": mensagem_id,
            "files_uploaded": len(files) if files else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        print("Error posting mensagem:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
