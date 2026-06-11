import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"A variável de ambiente {name} deve ser um inteiro.") from exc


# Configuração da API Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configuração da conexão com o banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = _get_int_env("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME", "Matriz")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
