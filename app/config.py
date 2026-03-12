import os
import warnings
from pathlib import Path

# Carregar .env apenas se existir (padrão de desenvolvimento)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv não está instalado; espera que variáveis sejam definidas no ambiente
    pass

# Banco de dados
HOST = os.getenv("HOST", "127.0.0.1:3306")
USER = os.getenv("USER", "root")
PASSWORD = os.getenv("PASSWORD", "root")
DATABASE = os.getenv("DATABASE", "projetofinal")

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20"))
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY or SECRET_KEY == "your_secret_key":
    warnings.warn(
        "SECRET_KEY não configurada! Defina uma chave segura na variável de ambiente SECRET_KEY.",
        stacklevel=2,
    )

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    or os.getenv("SUPABASE_SERVICE_ROLE", "")
    or os.getenv("SUPABASE_SERVICE_KEY", "")
    or os.getenv("SUPABASE_SECRET_KEY", "")
)
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "chamados-files")  # default plural