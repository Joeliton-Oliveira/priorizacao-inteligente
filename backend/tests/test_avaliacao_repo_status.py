# -*- coding: utf-8 -*-
"""Testes de status inicial no repositório de avaliação."""

from unittest.mock import patch

from db import avaliacao_repo


class _FakeCursor:
    def __init__(self, fetchone_values=None, fetchall_values=None):
        self.fetchone_values = list(fetchone_values or [])
        self.fetchall_values = list(fetchall_values or [])
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_values.pop(0)

    def fetchall(self):
        return self.fetchall_values.pop(0)


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_salvar_avaliacao_define_status_inicial_backlog():
    cursor = _FakeCursor(
        fetchone_values=[
            ("1.0.0",),  # SELECT versao_atual FROM projeto
            (101,),  # id_entrada_bruta
            (202,),  # id_requisito
            (303,),  # id_avaliacao
        ]
    )
    conn = _FakeConnection(cursor)
    respostas = [{"id_pergunta": 1, "texto": "Pergunta", "dimensao": "VALOR", "valor_resposta": 5}]

    with patch("db.avaliacao_repo.get_connection", return_value=conn):
        out = avaliacao_repo.salvar_avaliacao_completa(
            texto_original="texto",
            titulo_requisito="Titulo",
            descricao_requisito="Descricao",
            tipo_requisito="BUG",
            objetivo="Objetivo",
            finalidade="Finalidade",
            usuario_avaliador="qa",
            perfil_avaliador="analista",
            respostas=respostas,
            cadastro={"id_projeto": 1},
        )

    assert out["sucesso"] is True
    assert conn.committed is True

    sql_texts = [q for q, _ in cursor.executed]
    assert any("INSERT INTO status_requisito" in q for q in sql_texts)
    status_insert_params = [p for q, p in cursor.executed if "INSERT INTO status_requisito" in q][0]
    assert status_insert_params == (202,)


def test_listar_atividades_para_fila_fallback_sem_status_vai_para_backlog():
    rows = [
        (
            7,  # id_requisito
            "Item novo",
            "INCREMENTO",
            None,  # data_avaliacao
            "VALOR",  # dimensao
            3,  # valor_numerico
            None,  # status_atual vindo de LEFT JOIN sem linha
            11,  # id_projeto
            "Projeto X",
            "1.0.0",
        )
    ]
    cursor = _FakeCursor(fetchall_values=[rows])
    conn = _FakeConnection(cursor)

    with patch("db.avaliacao_repo.get_connection", return_value=conn):
        out = avaliacao_repo.listar_atividades_para_fila()

    assert len(out) == 1
    assert out[0]["status_atual"] == "BACKLOG"
