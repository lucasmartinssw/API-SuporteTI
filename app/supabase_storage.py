"""
Módulo para gerenciar uploads de arquivos no Supabase Storage
"""
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET
from fastapi import UploadFile
from typing import Optional
import uuid
from datetime import datetime

# Inicializar cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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
        url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        return url
    except Exception as e:
        raise Exception(f"Erro ao obter URL do arquivo: {str(e)}")
