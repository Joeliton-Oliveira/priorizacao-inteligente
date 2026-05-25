# Configuração da API Gemini
# GEMINI_API_KEY = "AIzaSyAp2Kd_zJd-vg-2_4NqQOyAeI528hPic2Y"  # chave antiga
GEMINI_API_KEY = "AIzaSyCFm--_wRWtUzb4DupvA4JyNTA1aAh7NxI"

# Configuração da conexão com o banco de dados
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "Matriz"
DB_USER = "postgres"
DB_PASSWORD = ""  # Sem senha

def get_connection_string():
    """Retorna a string de conexão PostgreSQL."""
    auth = f"{DB_USER}:{DB_PASSWORD}@" if DB_PASSWORD else f"{DB_USER}@"
    return f"postgresql://{auth}{DB_HOST}:{DB_PORT}/{DB_NAME}"
