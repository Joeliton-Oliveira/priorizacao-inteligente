# -*- coding: utf-8 -*-
"""Testes das rotas de projetos (mock do repositório — sem PostgreSQL)."""

import os

os.environ.setdefault("GEMINI_API_KEY", "test-key-fake")

from unittest.mock import patch
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


@patch("services.projetos_service.repo_listar_projetos")
def test_listar_projetos_vazio(mock_list):
    mock_list.return_value = []
    r = client.get("/api/v1/projetos")
    assert r.status_code == 200
    assert r.json() == []
    mock_list.assert_called_once_with(tipo_origem=None, status_projeto=None, busca_nome=None)


@patch("services.projetos_service.repo_listar_projetos")
def test_listar_projetos_filtro_novo(mock_list):
    mock_list.return_value = []
    r = client.get("/api/v1/projetos?tipo_origem=novo")
    assert r.status_code == 200
    mock_list.assert_called_once_with(tipo_origem="novo", status_projeto=None, busca_nome=None)


@patch("services.projetos_service.repo_listar_projetos")
def test_listar_projetos_filtro_status_e_q(mock_list):
    mock_list.return_value = []
    r = client.get("/api/v1/projetos?status=ativo&q=matriz")
    assert r.status_code == 200
    mock_list.assert_called_once_with(tipo_origem=None, status_projeto="ativo", busca_nome="matriz")


def test_listar_tipo_origem_query_invalida():
    r = client.get("/api/v1/projetos?tipo_origem=invalido")
    assert r.status_code == 422


def test_listar_status_query_invalido():
    r = client.get("/api/v1/projetos?status=foo")
    assert r.status_code == 422


@patch("services.projetos_service.repo_criar_projeto")
def test_criar_projeto_novo(mock_criar):
    mock_criar.return_value = {
        "id_projeto": 1,
        "nome_projeto": "Alpha",
        "tipo_origem": "novo",
        "versao_inicial": "1.0.0",
        "versao_atual": "1.0.0",
        "data_cadastro": "2026-01-01T00:00:00",
        "data_ultima_atualizacao": "2026-01-01T00:00:00",
    }
    r = client.post(
        "/api/v1/projetos",
        json={
            "nome_projeto": "Alpha",
            "tipo_origem": "novo",
        },
    )
    assert r.status_code == 200
    assert r.json()["versao_atual"] == "1.0.0"


@patch("services.projetos_service.repo_criar_projeto")
def test_criar_projeto_existente(mock_criar):
    mock_criar.return_value = {
        "id_projeto": 2,
        "nome_projeto": "XPTO",
        "tipo_origem": "existente",
        "versao_inicial": "3.11.52",
        "versao_atual": "3.11.52",
        "data_cadastro": "2026-01-01T00:00:00",
        "data_ultima_atualizacao": "2026-01-01T00:00:00",
    }
    r = client.post(
        "/api/v1/projetos",
        json={
            "nome_projeto": "XPTO",
            "tipo_origem": "existente",
            "versao_atual": "3.11.52",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["versao_inicial"] == "3.11.52"


def test_criar_projeto_existente_sem_versao_422():
    r = client.post(
        "/api/v1/projetos",
        json={
            "nome_projeto": "X",
            "tipo_origem": "existente",
        },
    )
    assert r.status_code == 422


@patch("services.projetos_service.repo_criar_projeto")
def test_criar_projeto_nome_duplicado(mock_criar):
    mock_criar.side_effect = ValueError("Já existe um projeto com esse nome.")
    r = client.post(
        "/api/v1/projetos",
        json={"nome_projeto": "Dup", "tipo_origem": "novo"},
    )
    assert r.status_code == 422


@patch("services.projetos_service.repo_listar_historico_projeto")
def test_historico_versao_vazio(mock_hist):
    mock_hist.return_value = []
    r = client.get("/api/v1/projetos/5/historico-versao")
    assert r.status_code == 200
    assert r.json() == []
    mock_hist.assert_called_once()
    assert mock_hist.call_args[0][0] == 5


@patch("services.projetos_service.repo_evoluir_projeto")
def test_evoluir_versao(mock_evo):
    mock_evo.return_value = {
        "id_projeto": 1,
        "nome_projeto": "Alpha",
        "versao_inicial": "1.0.0",
        "versao_atual": "1.0.1",
        "data_ultima_atualizacao": "2026-01-02T00:00:00",
    }
    r = client.post(
        "/api/v1/projetos/1/evoluir-versao",
        json={"nivel": "patch"},
    )
    assert r.status_code == 200
    assert r.json()["versao_atual"] == "1.0.1"


@patch("services.projetos_service.repo_evoluir_projeto")
def test_evoluir_versao_com_motivo(mock_evo):
    mock_evo.return_value = {
        "id_projeto": 1,
        "nome_projeto": "Alpha",
        "versao_inicial": "1.0.0",
        "versao_atual": "1.1.0",
        "data_ultima_atualizacao": "2026-01-02T00:00:00",
    }
    r = client.post(
        "/api/v1/projetos/1/evoluir-versao",
        json={
            "nivel": "minor",
            "motivo": "Nova funcionalidade",
            "usuario_responsavel": "Ana",
        },
    )
    assert r.status_code == 200
    mock_evo.assert_called_once_with(1, "minor", motivo="Nova funcionalidade", usuario_responsavel="Ana")


@patch("services.projetos_service.repo_evoluir_projeto")
def test_evoluir_projeto_nao_encontrado(mock_evo):
    mock_evo.side_effect = LookupError()
    r = client.post(
        "/api/v1/projetos/99/evoluir-versao",
        json={"nivel": "minor"},
    )
    assert r.status_code == 404


@patch("services.projetos_service.repo_atualizar_status_projeto")
def test_patch_status_projeto(mock_patch):
    mock_patch.return_value = {"id_projeto": 3, "nome_projeto": "X", "status_projeto": "arquivado"}
    r = client.patch("/api/v1/projetos/3/status", json={"status": "arquivado"})
    assert r.status_code == 200
    assert r.json()["status_projeto"] == "arquivado"
    mock_patch.assert_called_once_with(3, "arquivado")


@patch("services.projetos_service.repo_atualizar_status_projeto")
def test_patch_status_projeto_nao_encontrado(mock_patch):
    mock_patch.side_effect = LookupError()
    r = client.patch("/api/v1/projetos/99/status", json={"status": "ativo"})
    assert r.status_code == 404
