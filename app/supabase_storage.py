"""
Módulo para gerenciar uploads de arquivos no Supabase Storage
"""
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_BUCKET
from fastapi import UploadFile
from typing import Optional
import uuid
from datetime import datetime


def _resolve_supabase_server_key() -> str:
    """Resolve and sanitize server-side key used for Storage operations."""
    raw_key = (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY or "").strip()

    # Aceita formato "Bearer <token>" vindo de cópia de headers.
    if raw_key.lower().startswith("bearer "):
        raw_key = raw_key[7:].strip()

    # Chaves publishable não funcionam para upload no backend via Storage.
    if raw_key.startswith("sb_publishable_"):
        raise RuntimeError(
            "SUPABASE_KEY inválida para upload. Use SUPABASE_SERVICE_ROLE_KEY "
            "(ou SUPABASE_KEY com service_role/secret key do projeto)."
        )

    if not raw_key:
        raise RuntimeError(
            "Chave Supabase ausente. Defina SUPABASE_SERVICE_ROLE_KEY "
            "(ou SUPABASE_SERVICE_KEY / SUPABASE_SECRET_KEY) no .env"
        )

    return raw_key

def _get_supabase_client() -> Client:
    """Create Supabase client lazily to avoid import-time crashes."""
    return create_client(SUPABASE_URL, _resolve_supabase_server_key())


def upload_file_to_supabase(
    file: UploadFile,
    chamado_id: int,
    mensagem_id: Optional[int] = None
) -> dict:
    """
    Faz upload de arquivo para Supabase Storage
    
    Args:
        file: UploadFile do FastAPI
        chamado_id: ID do chamado associado
        mensagem_id: ID da mensagem (opcional)
    
    Returns:
        dict com informações do arquivo uploaded:
        {
            'url': URL pública do arquivo,
            'file_path': caminho armazenado,
            'file_name': nome original,
            'content_type': tipo MIME
        }
    """
    try:
        # Gerar nome único para o arquivo
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Estrutura de pastas: chamados/{chamado_id}/{tipo}/{arquivo}
        folder_type = f"mensagem_{mensagem_id}" if mensagem_id else "descricao"
        file_path = f"chamados/{chamado_id}/{folder_type}/{timestamp}_{unique_id}.{file_extension}"
        
        # Ler conteúdo do arquivo
        file_content = file.file.read()
        
        # Upload para Supabase Storage
        supabase = _get_supabase_client()
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Gerar URL pública para o arquivo
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        
        return {
            'url': public_url,
            'file_path': file_path,
            'file_name': file.filename,
            'content_type': file.content_type,
            'uploaded_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise Exception(f"Erro ao fazer upload do arquivo: {str(e)}")


def delete_file_from_supabase(file_path: str) -> bool:
    """
    Deleta arquivo do Supabase Storage
    
    Args:
        file_path: caminho do arquivo no storage
    
    Returns:
        True se deletado com sucesso
    """
    try:
        supabase = _get_supabase_client()
        supabase.storage.from_(SUPABASE_BUCKET).remove([file_path])
        return True
    except Exception as e:
        print(f"Erro ao deletar arquivo: {str(e)}")
        return False


def get_public_url(file_path: str) -> str:
    """
    Obtém URL pública de um arquivo
    
    Args:
        file_path: caminho do arquivo no storage
    
    Returns:
        URL pública do arquivo
    """
    try:
        supabase = _get_supabase_client()
        url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        return url
    except Exception as e:
        raise Exception(f"Erro ao obter URL do arquivo: {str(e)}")
