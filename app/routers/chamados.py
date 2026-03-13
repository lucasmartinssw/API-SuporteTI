import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from app.models import ChamadoCreate, ChamadoOut, MensagemCreate
from app.auth import get_current_user
from app.database import get_db_cursor, get_db_connection
from app.supabase_storage import upload_file_to_supabase, delete_file_from_supabase
from app.routers.notificacoes import create_notificacao
from app.routers.auditoria import log_auditoria
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
            "SELECT id, url_arquivo as url, tipo_arquivo as type, nome_arquivo as name FROM chamados_midia WHERE chamado_id = %s AND mensagem_id IS NULL", 
            (chamado_id,)
        )
        arquivos = cursor.fetchall()
        
        attachments = []
        for arquivo in arquivos:
            fallback_name = arquivo['url'].split('/')[-1] if arquivo.get('url') else f"arquivo_{arquivo['id']}"
            attachments.append({
                'id': str(arquivo['id']),
                'url': arquivo['url'],
                'name': arquivo.get('name') or fallback_name,
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
            "SELECT id, url_arquivo as url, tipo_arquivo as type, nome_arquivo as name FROM chamados_midia WHERE mensagem_id = %s", 
            (mensagem_id,)
        )
        arquivos = cursor.fetchall()
        attachments = []
        for arquivo in arquivos:
            fallback_name = arquivo['url'].split('/')[-1] if arquivo.get('url') else f"arquivo_{arquivo['id']}"
            attachments.append({
                'id': str(arquivo['id']),
                'url': arquivo['url'],
                'name': arquivo.get('name') or fallback_name,
                'type': arquivo['type']
            })
        return attachments
    except Exception as e:
        print(f"Error getting message attachments: {str(e)}")
        return []




def get_tecnicos_for_chamado(chamado_id: int, cursor) -> list:
    """Get list of technicians assigned to a chamado."""
    try:
        cursor.execute(
            "SELECT u.id, u.nome, LOWER(u.email) AS email FROM chamados_tecnicos ct "
            "JOIN users u ON u.id = ct.user_id "
            "WHERE ct.chamado_id = %s",
            (chamado_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting tecnicos: {str(e)}")
        return []

def get_chamado_with_access_check(chamado_id: int, current_user: dict, cursor) -> dict:
    """Return chamado row if user can access it, otherwise raise HTTPException."""
    cursor.execute("SELECT id, user_id FROM chamados WHERE id = %s", (chamado_id,))
    chamado = cursor.fetchone()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

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
    
    # Add attachments and technicians to each chamado
    for chamado in chamados:
        chamado['attachments'] = get_attachments_for_chamado(chamado['id'], cursor)
        chamado['tecnicos'] = get_tecnicos_for_chamado(chamado['id'], cursor)
    
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

        # Notify all technicians and admins
        try:
            cursor.execute("SELECT id FROM users WHERE cargo IN ('tecnico', 'admin')")
            techs = cursor.fetchall()
            for tech in techs:
                create_notificacao(tech['id'], 'ticket_created', chamado_id,
                    f"Novo chamado aberto: {chamado.title}", cursor, conn)
        except Exception as ne:
            print(f"Notification error: {ne}")

        # Audit log
        if chamado_id:
            log_auditoria('chamados', chamado_id, user_id, 'criado',
                f"Chamado criado: {chamado.title}", cursor, conn)

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
        upload_errors = []
        files_uploaded = 0
        if files:
            for upload in files:
                try:
                    # Upload file to Supabase
                    file_info = upload_file_to_supabase(upload, chamado_id)
                    
                    # Save metadata in database
                    cursor.execute(
                        "INSERT INTO chamados_midia (chamado_id, url_arquivo, tipo_arquivo, nome_arquivo) VALUES (%s, %s, %s, %s)",
                        (chamado_id, file_info['url'], file_info['content_type'], file_info['file_name'])
                    )
                    files_uploaded += 1
                except Exception as e:
                    print("Error uploading file to Supabase:", str(e))
                    traceback.print_exc()
                    upload_errors.append({
                        "file_name": getattr(upload, "filename", "arquivo"),
                        "error": str(e)
                    })
            
            conn.commit()

        response = {
            "message": "Chamado criado com sucesso",
            "id": chamado_id,
            "files_uploaded": files_uploaded,
            "files_failed": len(upload_errors)
        }

        if upload_errors:
            response["warnings"] = [
                "Um ou mais anexos falharam no upload. Configure SUPABASE_SERVICE_ROLE_KEY no .env para uploads via backend."
            ]
            response["upload_errors"] = upload_errors

        # Notify all technicians and admins
        try:
            cursor.execute("SELECT id FROM users WHERE cargo IN ('tecnico', 'admin')")
            techs = cursor.fetchall()
            for tech in techs:
                create_notificacao(tech['id'], 'ticket_created', chamado_id,
                    f"Novo chamado aberto: {title}", cursor, conn)
        except Exception as ne:
            print(f"Notification error: {ne}")

        # Audit log
        log_auditoria('chamados', chamado_id, user_id, 'criado',
            f"Chamado criado: {title}", cursor, conn)

        return response
    except HTTPException:
        raise
    except Exception as e:
        print("Error creating chamado:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{chamado_id}")
def get_chamado(chamado_id: int, current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor)):
    get_chamado_with_access_check(chamado_id, current_user, cursor)

    cursor.execute(
        "SELECT c.*, LOWER(u.email) AS user_email "
        "FROM chamados c "
        "LEFT JOIN users u ON u.id = c.user_id "
        "WHERE c.id = %s",
        (chamado_id,)
    )
    chamado = cursor.fetchone()

    chamado['attachments'] = get_attachments_for_chamado(chamado_id, cursor)
    chamado['tecnicos'] = get_tecnicos_for_chamado(chamado_id, cursor)
    return chamado


@router.patch("/{chamado_id}")
def update_chamado(chamado_id: int, data: dict, current_user: dict = Depends(get_current_user), cursor = Depends(get_db_cursor), conn = Depends(get_db_connection)):
    user_cargo = current_user.get('cargo')
    user_id = current_user.get('id')

    # Fetch chamado to check ownership
    cursor.execute("SELECT user_id, status_id, titulo FROM chamados WHERE id = %s", (chamado_id,))
    chamado = cursor.fetchone()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    is_owner = chamado['user_id'] == user_id
    is_tech = user_cargo in ('admin', 'tecnico')

    # Users can only close (3) or reopen (1) their own tickets
    if not is_tech:
        if not is_owner:
            raise HTTPException(status_code=403, detail="Sem permissão")
        new_status = data.get('status_id')
        if new_status not in (1, 3):
            raise HTTPException(status_code=403, detail="Usuários só podem fechar ou reabrir chamados")
        allowed = {'status_id': new_status}
    else:
        allowed = {k: v for k, v in data.items() if k in ('status_id', 'prioridade_id')}

    if not allowed:
        raise HTTPException(status_code=400, detail="Nenhum campo atualizável fornecido")

    set_clause = ", ".join([f"{k} = %s" for k in allowed.keys()])
    values = list(allowed.values())
    values.append(chamado_id)
    cursor.execute(f"UPDATE chamados SET {set_clause}, updated_at = NOW() WHERE id = %s", tuple(values))
    conn.commit()

    # Send status/priority notifications and audit
    actor_name = current_user.get('nome') or current_user.get('email', 'Usuário')
    if 'status_id' in allowed:
        status_labels = {1: 'Aberto', 2: 'Em Atendimento', 3: 'Concluído', 4: 'Fechado'}
        new_label = status_labels.get(allowed['status_id'], 'Atualizado')
        try:
            if is_tech:
                create_notificacao(chamado['user_id'], 'status_change', chamado_id,
                    f"Seu chamado '{chamado['titulo']}' foi atualizado para: {new_label}", cursor, conn)
            else:
                cursor.execute(
                    "SELECT user_id FROM chamados_tecnicos WHERE chamado_id = %s", (chamado_id,))
                for row in cursor.fetchall():
                    create_notificacao(row['user_id'], 'status_change', chamado_id,
                        f"Chamado '{chamado['titulo']}' foi {new_label.lower()} pelo usuário", cursor, conn)
        except Exception as ne:
            print(f"Notification error: {ne}")
        log_auditoria('chamados', chamado_id, user_id, 'status_alterado',
            f"Status alterado para '{new_label}' por {actor_name}", cursor, conn)

    if 'prioridade_id' in allowed:
        prio_labels = {1: 'Baixa', 2: 'Média', 3: 'Alta', 4: 'Urgente'}
        new_prio = prio_labels.get(allowed['prioridade_id'], 'Atualizada')
        log_auditoria('chamados', chamado_id, user_id, 'prioridade_alterada',
            f"Prioridade alterada para '{new_prio}' por {actor_name}", cursor, conn)

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
    mensagem: str = Form("", description="Conteúdo da mensagem/resposta"),
    is_internal: bool = Form(False, description="Se a mensagem é interna (visível apenas para TI)"),
    files: Optional[List[UploadFile]] = File(default=None, description="Arquivos anexos (opcional)"),
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Post message with optional file attachments using Supabase Storage"""
    get_chamado_with_access_check(chamado_id, current_user, cursor)

    mensagem = (mensagem or "").strip()

    user_cargo = current_user.get('cargo')
    if is_internal and user_cargo not in ('admin', 'tecnico'):
        raise HTTPException(status_code=403, detail="Apenas a equipe de TI pode enviar mensagens internas")

    # Normalise files list before we check it
    if files is None:
        files = []
    elif isinstance(files, str):
        files = []
    elif isinstance(files, list):
        files = [f for f in files if not isinstance(f, str)]

    if not mensagem and not files:
        raise HTTPException(status_code=400, detail="Mensagem ou arquivo obrigatório.")

    user_id = current_user.get('id')
    
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
                        "INSERT INTO chamados_midia (chamado_id, mensagem_id, url_arquivo, tipo_arquivo, nome_arquivo) VALUES (%s, %s, %s, %s, %s)",
                        (chamado_id, mensagem_id, file_info['url'], file_info['content_type'], file_info['file_name'])
                    )
                except Exception as e:
                    print("Error uploading file to Supabase:", str(e))
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=f"Error uploading attachment: {str(e)}")
            
            conn.commit()

        # Notify the other party
        try:
            cursor.execute("SELECT user_id, titulo FROM chamados WHERE id = %s", (chamado_id,))
            ch = cursor.fetchone()
            if ch:
                if user_cargo in ('admin', 'tecnico'):
                    # Tech wrote — notify ticket owner
                    create_notificacao(ch['user_id'], 'new_message', chamado_id,
                        f"Nova resposta da equipe de TI no chamado '{ch['titulo']}'", cursor, conn)
                else:
                    # User wrote — notify assigned techs
                    cursor.execute("SELECT user_id FROM chamados_tecnicos WHERE chamado_id = %s", (chamado_id,))
                    for row in cursor.fetchall():
                        create_notificacao(row['user_id'], 'new_message', chamado_id,
                            f"Nova mensagem do usuário no chamado '{ch['titulo']}'", cursor, conn)
        except Exception as ne:
            print(f"Notification error: {ne}")

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

@router.post("/{chamado_id}/tecnicos/{user_id}", status_code=status.HTTP_201_CREATED)
def add_tecnico(
    chamado_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Assign a technician to a chamado."""
    if current_user.get('cargo') not in ('admin', 'tecnico'):
        raise HTTPException(status_code=403, detail="Apenas técnicos ou admins podem atribuir técnicos")
    get_chamado_with_access_check(chamado_id, current_user, cursor)
    # Check user exists and is a tech/admin
    cursor.execute("SELECT id, cargo FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user['cargo'] not in ('admin', 'tecnico'):
        raise HTTPException(status_code=400, detail="Usuário não é técnico ou admin")
    try:
        cursor.execute(
            "INSERT IGNORE INTO chamados_tecnicos (chamado_id, user_id) VALUES (%s, %s)",
            (chamado_id, user_id)
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    cursor.execute("SELECT nome FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    tech_name = row['nome'] if row else f"#{user_id}"
    actor = current_user.get('nome') or current_user.get('email', '')
    log_auditoria('chamados', chamado_id, current_user['id'], 'tecnico_adicionado',
        f"{tech_name} adicionado por {actor}", cursor, conn)
    return {"message": "Técnico adicionado"}


@router.delete("/{chamado_id}/tecnicos/{user_id}")
def remove_tecnico(
    chamado_id: int,
    user_id: int,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Remove a technician from a chamado."""
    if current_user.get('cargo') not in ('admin', 'tecnico'):
        raise HTTPException(status_code=403, detail="Apenas técnicos ou admins podem remover técnicos")
    get_chamado_with_access_check(chamado_id, current_user, cursor)
    cursor.execute(
        "DELETE FROM chamados_tecnicos WHERE chamado_id = %s AND user_id = %s",
        (chamado_id, user_id)
    )
    conn.commit()
    cursor.execute("SELECT nome FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    tech_name = row['nome'] if row else f"#{user_id}"
    actor = current_user.get('nome') or current_user.get('email', '')
    log_auditoria('chamados', chamado_id, current_user['id'], 'tecnico_removido',
        f"{tech_name} removido por {actor}", cursor, conn)
    return {"message": "Técnico removido"}


@router.delete("/{chamado_id}/mensagens/{mensagem_id}")
def delete_mensagem(
    chamado_id: int,
    mensagem_id: int,
    current_user: dict = Depends(get_current_user),
    cursor = Depends(get_db_cursor),
    conn = Depends(get_db_connection)
):
    """Delete a message — admin only."""
    if current_user.get('cargo') not in ('admin', 'tecnico'):
        raise HTTPException(status_code=403, detail="Apenas técnicos e admins podem apagar mensagens")

    # Verify message belongs to this chamado
    cursor.execute(
        "SELECT id FROM chamados_mensagens WHERE id = %s AND chamado_id = %s",
        (mensagem_id, chamado_id)
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")

    # Delete attached media first (FK constraint)
    cursor.execute("DELETE FROM chamados_midia WHERE mensagem_id = %s", (mensagem_id,))
    cursor.execute("DELETE FROM chamados_mensagens WHERE id = %s", (mensagem_id,))
    conn.commit()
    actor = current_user.get('nome') or current_user.get('email', '')
    log_auditoria('chamados', chamado_id, current_user['id'], 'mensagem_apagada',
        f"Mensagem #{mensagem_id} apagada por {actor}", cursor, conn)
    return {"message": "Mensagem apagada"}