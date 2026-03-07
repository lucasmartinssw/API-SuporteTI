import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from ..models import ChamadoCreate, ChamadoOut, MensagemCreate
from ..auth import get_current_user
from ..database import get_db_cursor, get_db_connection
from ..supabase_storage import upload_file_to_supabase, delete_file_from_supabase
import traceback

router = APIRouter(prefix="/chamados", tags=["Chamados"])

# ──── Helper functions ────────────────────────────
def get_priority_id(priority: str) -> int:
    """Map priority string to priority ID"""
    priority_map = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'urgent': 4
    }
    return priority_map.get(priority.lower(), 2)  # Default to medium

def get_category_id(category: str, cursor, conn) -> int:
    """Get category ID by name, creating it if it doesn't exist"""
    try:
        # Try to find the exact category
        cursor.execute("SELECT id FROM categorias WHERE nome = %s", (category,))
        result = cursor.fetchone()
        if result:
            return result['id']
        
        # If category doesn't exist, create it
        cursor.execute("INSERT INTO categorias (nome) VALUES (%s)", (category,))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error getting category ID: {str(e)}")
        # Try fallback to 'Outros'
        try:
            cursor.execute("SELECT id FROM categorias WHERE nome = 'Outros'")
            result = cursor.fetchone()
            if result:
                return result['id']
            # If 'Outros' doesn't exist, create it
            cursor.execute("INSERT INTO categorias (nome) VALUES (%s)", ('Outros',))
            conn.commit()
            return cursor.lastrowid
        except Exception as fallback_error:
            raise HTTPException(status_code=500, detail=f"Error processing category: {str(fallback_error)}")

def get_attachments_for_chamado(chamado_id, cursor) -> list:
    """Get attachments for a chamado from chamados_midia table (excluding message files)"""
    try:
        cursor.execute(
            "SELECT id, url_arquivo as url, tipo_arquivo as type FROM chamados_midia WHERE chamado_id = %s AND mensagem_id IS NULL", 
            (chamado_id,)
        )
        arquivos = cursor.fetchall()
        
        attachments = []
        for arquivo in arquivos:
            # Extract filename from URL or use generic name
            url_parts = arquivo['url'].split('/')
            filename = url_parts[-1] if url_parts else f"arquivo_{arquivo['id']}"
            attachments.append({
                'id': str(arquivo['id']),
                'url': arquivo['url'],
                'name': filename,
                'type': arquivo['type']
            })
        return attachments
    except Exception as e:
        print(f"Error getting attachments: {str(e)}")
        return []


# ──── Message helpers ───────────────────────────────

def get_attachments_for_mensagem(mensagem_id, cursor) -> list:
    """Get attachments associated with a specific mensagem_id"""
    try:
        cursor.execute(
            "SELECT id, url_arquivo as url, tipo_arquivo as type FROM chamados_midia WHERE mensagem_id = %s", 
            (mensagem_id,)
        )
        arquivos = cursor.fetchall()
        attachments = []
        for arquivo in arquivos:
            url_parts = arquivo['url'].split('/')
            filename = url_parts[-1] if url_parts else f"arquivo_{arquivo['id']}"
            attachments.append({
                'id': str(arquivo['id']),
                'url': arquivo['url'],
                'name': filename,
                'type': arquivo['type']
            })
        return attachments
    except Exception as e:
        print(f"Error getting message attachments: {str(e)}")
        return []


def get_chamado_with_access_check(chamado_id: int, current_user: dict, cursor) -> dict:
    """Return chamado row if user can access it, otherwise raise HTTPException."""
    cursor.execute("SELECT id, user_id FROM chamados WHERE id = %s", (chamado_id,))
    chamado = cursor.fetchone()
    if not chamado:
        raise HTTPException(status_code=404, detail=f"Chamado {chamado_id} not found")

    user_cargo = current_user.get('cargo')
    user_id = current_user.get('id')
    if user_cargo not in ('admin', 'tecnico') and chamado.get('user_id') != user_id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para acessar este chamado")

    return chamado

# ──────────────────────────────────────────────────


@router.get("")
def list_chamados(current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor)):
    user_id = current_user.get('id')
    user_cargo = current_user.get('cargo')

    base_query = (
        "SELECT c.*, LOWER(u.email) AS user_email, cat.nome AS categoria "
        "FROM chamados c "
        "LEFT JOIN users u ON u.id = c.user_id "
        "LEFT JOIN categorias cat ON cat.id = c.categoria_id"
    )

    if user_cargo in ('admin', 'tecnico'):
        cursor.execute(base_query)
    else:
        cursor.execute(f"{base_query} WHERE c.user_id = %s", (user_id,))

    chamados = cursor.fetchall()
    
    # Add attachments to each chamado
    for chamado in chamados:
        chamado['attachments'] = get_attachments_for_chamado(chamado['id'], cursor)
    
    return chamados


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
        # Get priority and category IDs
        priority_id = get_priority_id(chamado.priority)
        category_id = get_category_id(chamado.category, cursor, conn)

        cursor.execute(
            "INSERT INTO chamados (titulo, descricao, user_id, categoria_id, status_id, prioridade_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (chamado.title, chamado.description, user_id, category_id, 1, priority_id)
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
    priority: str = Form("medium", description="Prioridade: low, medium, high, urgent"),
    category: str = Form("Outros", description="Categoria do chamado"),
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
        # Get priority and category IDs
        priority_id = get_priority_id(priority)
        category_id = get_category_id(category, cursor, conn)

        # Insert chamado in database
        cursor.execute(
            "INSERT INTO chamados (titulo, descricao, user_id, categoria_id, status_id, prioridade_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (title, description, user_id, category_id, 1, priority_id)
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
    get_chamado_with_access_check(chamado_id, current_user, cursor)

    cursor.execute("SELECT * FROM chamados WHERE id = %s", (chamado_id,))
    chamado = cursor.fetchone()

    # Get attachments using helper function
    chamado['attachments'] = get_attachments_for_chamado(chamado_id, cursor)
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
    get_chamado_with_access_check(chamado_id, current_user, cursor)
    
    # Join with users to fetch author name and email
    cursor.execute(
        "SELECT m.id, m.chamado_id, m.user_id, u.nome AS author_name, LOWER(u.email) AS author_email, m.mensagem, m.enviado_em, m.is_internal "
        "FROM chamados_mensagens m "
        "LEFT JOIN users u ON u.id = m.user_id "
        "WHERE m.chamado_id = %s "
        "ORDER BY m.enviado_em",
        (chamado_id,)
    )
    mensagens = cursor.fetchall()

    # Attach attachments for each message
    for msg in mensagens:
        msg['attachments'] = get_attachments_for_mensagem(msg['id'], cursor)

    return mensagens


@router.post("/{chamado_id}/mensagens", status_code=status.HTTP_201_CREATED)
def post_mensagem(
    chamado_id: int,
    mensagem: str = Form(..., description="Conteúdo da mensagem/resposta"),
    is_internal: bool = Form(False, description="Se a mensagem é interna (visível apenas para TI)"),
    files: Optional[List[UploadFile]] = File(default=None, description="Arquivos anexos (opcional)"),
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Post message with optional file attachments using Supabase Storage"""
    get_chamado_with_access_check(chamado_id, current_user, cursor)

    user_cargo = current_user.get('cargo')
    if is_internal and user_cargo not in ('admin', 'tecnico'):
        raise HTTPException(status_code=403, detail="Apenas a equipe de TI pode enviar mensagens internas")
    
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
            "INSERT INTO chamados_mensagens (chamado_id, user_id, mensagem, enviado_em, is_internal) VALUES (%s, %s, %s, NOW(), %s)",
            (chamado_id, user_id, mensagem, is_internal)
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
