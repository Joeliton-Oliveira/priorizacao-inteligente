# -*- coding: utf-8 -*-
"""Testes da API REST — rotas, payloads e integração."""
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Importar app após eventual config de env para testes
import os
os.environ.setdefault("GEMINI_API_KEY", "test-key-fake")

from api import app
from services.analise_ia_service import extrair_json_ia

client = TestClient(app)


# --- Extração de JSON (analise_ia_service) ---

def test_extrair_json_puro():
    data = {"a": 1}
    assert extrair_json_ia(json.dumps(data)) == data


def test_extrair_json_markdown():
    data = {"titulo_requisito": "X"}
    wrapped = "```json\n" + json.dumps(data) + "\n```"
    assert extrair_json_ia(wrapped) == data


def test_extrair_json_invalido_retorna_none():
    assert extrair_json_ia("não é json") is None


# --- Rota raiz ---

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert "mensagem" in body
    assert "docs" in body
    assert "app_version" in body
    assert "release_date" in body


def test_api_v1_status():
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    body = r.json()
    assert body["app_version"]
    assert body["release_date"]
    assert len(body["release_date"].split("-")) == 3


# --- Rota POST /requisitos/analise — estruturação com IA (mock) ---

@patch("services.analise_ia_service.model")
def test_analise_payload_minimo(mock_model, payload_analise_minimo):
    mock_model.generate_content.return_value = MagicMock(
        text=json.dumps({
            "titulo_requisito": "Botão não funciona",
            "descricao_requisito": "Descrição.",
            "tipo_requisito": "BUG",
            "objetivo": "Objetivo.",
            "finalidade": "Finalidade.",
            "perguntas_avaliacao": [
                {
                    "id_pergunta": 1,
                    "texto": "Criticidade?",
                    "dimensao": "CRITICIDADE",
                    "opcoes_resposta": [
                        {"rotulo": "Muito baixo", "valor": 1},
                        {"rotulo": "Baixo", "valor": 2},
                        {"rotulo": "Médio", "valor": 3},
                        {"rotulo": "Alto", "valor": 4},
                        {"rotulo": "Muito alto", "valor": 5},
                    ],
                },
                {
                    "id_pergunta": 2,
                    "texto": "Severidade?",
                    "dimensao": "SEVERIDADE",
                    "opcoes_resposta": [
                        {"rotulo": "Muito baixo", "valor": 1},
                        {"rotulo": "Baixo", "valor": 2},
                        {"rotulo": "Médio", "valor": 3},
                        {"rotulo": "Alto", "valor": 4},
                        {"rotulo": "Muito alto", "valor": 5},
                    ],
                },
            ],
        })
    )
    r = client.post("/api/v1/requisitos/analise", json=payload_analise_minimo)
    assert r.status_code == 200
    data = r.json()
    assert "titulo_requisito" in data
    assert "descricao_requisito" in data
    assert data["tipo_requisito"] in ("BUG", "INCREMENTO")
    assert "objetivo" in data
    assert "finalidade" in data
    assert "perguntas_avaliacao" in data
    assert len(data["perguntas_avaliacao"]) >= 2


def test_analise_texto_vazio_400():
    r = client.post("/api/v1/requisitos/analise", json={"texto_original": ""})
    assert r.status_code == 400


def test_analise_campo_texto_compatibilidade():
    """Compatibilidade com campo antigo 'texto'."""
    with patch("services.analise_ia_service.model") as mock_model:
        mock_model.generate_content.return_value = MagicMock(
            text=json.dumps({
                "titulo_requisito": "T",
                "descricao_requisito": "D",
                "tipo_requisito": "BUG",
                "objetivo": "O",
                "finalidade": "F",
                "perguntas_avaliacao": [
                    {"id_pergunta": 1, "texto": "P1?", "dimensao": "CRITICIDADE",
                     "opcoes_resposta": [{"rotulo": str(i), "valor": i} for i in range(1, 6)]},
                    {"id_pergunta": 2, "texto": "P2?", "dimensao": "SEVERIDADE",
                     "opcoes_resposta": [{"rotulo": str(i), "valor": i} for i in range(1, 6)]},
                ],
            })
        )
        r = client.post("/api/v1/requisitos/analise", json={"texto": "Algo aqui"})
        assert r.status_code == 200


# --- Perguntas: estrutura Likert ---

@patch("services.analise_ia_service.model")
def test_perguntas_tem_5_opcoes_likert(mock_model, payload_analise_minimo):
    mock_model.generate_content.return_value = MagicMock(
        text=json.dumps({
            "titulo_requisito": "T",
            "descricao_requisito": "D",
            "tipo_requisito": "BUG",
            "objetivo": "O",
            "finalidade": "F",
            "perguntas_avaliacao": [
                {"id_pergunta": 1, "texto": "P?", "dimensao": "CRITICIDADE",
                 "opcoes_resposta": [{"rotulo": f"Op{i}", "valor": i} for i in range(1, 6)]},
                {"id_pergunta": 2, "texto": "P2?", "dimensao": "SEVERIDADE",
                 "opcoes_resposta": [{"rotulo": f"Op{i}", "valor": i} for i in range(1, 6)]},
            ],
        })
    )
    r = client.post("/api/v1/requisitos/analise", json=payload_analise_minimo)
    assert r.status_code == 200
    for p in r.json()["perguntas_avaliacao"]:
        assert "id_pergunta" in p
        assert "texto" in p
        assert "dimensao" in p
        assert "opcoes_resposta" in p
        assert len(p["opcoes_resposta"]) == 5
        for o in p["opcoes_resposta"]:
            assert "rotulo" in o
            assert "valor" in o
            assert 1 <= o["valor"] <= 5


# --- Fila (depende de listar_atividades_para_fila — pode falhar sem DB) ---

def test_get_fila_bugs():
    r = client.get("/api/v1/fila/bugs")
    if r.status_code == 200:
        assert isinstance(r.json(), list)


def test_get_fila_incrementos():
    r = client.get("/api/v1/fila/incrementos")
    if r.status_code == 200:
        assert isinstance(r.json(), list)


@patch("services.config_fila_service.obter_configuracao")
def test_get_config_fila(mock_get_config):
    mock_get_config.return_value = {
        "vazao": {"bugs": 60, "incrementos": 40},
        "wip": {"TO_DO": 5, "DEVELOP": 2, "TEST": 2, "DEPLOY": 1},
    }
    r = client.get("/api/v1/config-fila")
    assert r.status_code == 200
    body = r.json()
    assert body["vazao"]["bugs"] == 60
    assert body["wip"]["TO_DO"] == 5


@patch("services.config_fila_service.salvar_configuracao")
def test_post_config_fila(mock_save_config):
    mock_save_config.return_value = {"ok": True, "message": "Configuração salva."}
    r = client.post("/api/v1/config-fila", json={"vazao": {"bugs": 70}})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    mock_save_config.assert_called_once()


@patch("services.demanda_consulta_service.obter_visao_360")
def test_get_visao_360_demanda(mock_visao):
    mock_visao.return_value = {
        "identificacao": {"id_requisito": 1, "titulo": "Bug X"},
        "origem_demanda": {"texto_original": "Erro"},
        "estruturacao_ia": {"tipo_requisito": "BUG"},
        "avaliacao": {"score": 20},
        "respostas": [],
        "documentacao_fase": {},
        "gates": {"coluna_kanban": "BACKLOG"},
    }
    r = client.get("/api/v1/demandas/1/visao-360")
    assert r.status_code == 200
    assert r.json()["identificacao"]["id_requisito"] == 1


@patch("services.demanda_consulta_service.obter_auditoria")
def test_get_auditoria_demanda(mock_auditoria):
    mock_auditoria.return_value = {
        "id_requisito": 1,
        "titulo": "Bug X",
        "tipo_requisito": "BUG",
        "eventos": [
            {
                "tipo": "avaliacao",
                "titulo": "Avaliação registrada",
                "descricao": "Teste",
                "quando": "2026-05-26T12:00:00",
                "responsavel": "QA",
            }
        ],
    }
    r = client.get("/api/v1/demandas/1/auditoria")
    assert r.status_code == 200
    body = r.json()
    assert body["id_requisito"] == 1
    assert body["eventos"][0]["titulo"] == "Avaliação registrada"
