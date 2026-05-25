"""
Conexão com o banco de dados PostgreSQL.
Banco: Matriz
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2 import OperationalError

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    """
    Abre e retorna uma conexão com o PostgreSQL.
    Configuração: banco Matriz, sem senha.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD or None,
        )
        return conn
    except OperationalError as e:
        raise OperationalError(f"Erro ao conectar ao banco Matriz: {e}") from e


def test_connection():
    """Testa a conexão com o banco e retorna True se OK."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    if test_connection():
        print("Conexão com o banco Matriz estabelecida com sucesso.")
    else:
        print("Falha na conexão com o banco Matriz.")
