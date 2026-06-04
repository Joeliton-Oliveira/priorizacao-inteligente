"""
Executa o seed inicial na subida da API quando o banco está vazio.
"""
from __future__ import annotations

import os

from db.connection import get_connection


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def contar_projetos() -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM projeto")
            row = cur.fetchone()
            return int(row[0]) if row else 0
    finally:
        conn.close()


def executar_seed_inicial_se_necessario(*, force: bool = False) -> bool:
    """
    Retorna True se o seed foi executado nesta chamada.
    """
    if not force and contar_projetos() > 0:
        return False

    from db.seed_inicial import executar_seed

    executar_seed(force=force)
    return True
