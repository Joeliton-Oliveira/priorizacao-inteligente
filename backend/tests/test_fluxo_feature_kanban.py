# -*- coding: utf-8 -*-
"""
Bateria: fluxo de feature (INCREMENTO), Kanban por baia e gates documentais.
Sem PostgreSQL — mock de `db.*` nos pontos usados pela API.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GEMINI_API_KEY", "test-key-fake")

from api import app
from db.doc_fase_repo import (
    FASES_DOC_VALIDAS,
    serialize_casos_teste_conteudo,
    serialize_deploy_conteudo,
    serialize_doc_requisito_completo,
    serialize_entrega_dev_conteudo,
    serialize_prontidao_dev_conteudo,
)
from services.kanban_gates import PRONTIDAO_CHECKLIST_VALORES

client = TestClient(app)

RID = 501


def _fases_vazias() -> dict[str, str]:
    return {k: "" for k in FASES_DOC_VALIDAS}


def _doc_requisito_completo() -> str:
    return serialize_doc_requisito_completo(
        {
            "nome_funcionalidade": "Dashboard comercial",
            "descricao_detalhada": "Indicadores de vendas e metas.",
            "restricoes": "Nenhuma",
        },
        rf=["O utilizador vê gráfico de vendas."],
        rnf=["Tempo de resposta < 2s."],
        regras=["Apenas perfil gestor altera metas."],
        criterios=["Dado utilizador gestor, quando abre o dashboard, então vê KPIs."],
    )


def _prontidao_completa() -> str:
    return serialize_prontidao_dev_conteudo(
        {
            "responsavel_desenvolvimento": "Dev Silva",
            "registrado_por": "PO Costa",
            "data_prontidao": "2026-04-02",
            "checklist": list(PRONTIDAO_CHECKLIST_VALORES),
        },
        RID,
    )


def _entrega_completa() -> str:
    return serialize_entrega_dev_conteudo(
        {
            "nome_entrega": "Dashboard v1",
            "descricao_desenvolvido": "Gráficos e filtros.",
            "alteracoes": "Novo módulo.",
            "validacao_qa": "Validar filtros por região.",
            "branch_referencia": "feature/dashboard",
            "commit_referencia": "abc123",
            "desenvolvedor": "Dev Silva",
            "data_entrega_teste": "2026-04-03",
        },
        RID,
    )


def _casos_teste_aprovado() -> str:
    caso = {
        "resumo": "Filtro por mês",
        "passos": "1. Abrir dashboard 2. Filtrar abril",
        "resultado_esperado": "Dados de abril",
        "resultado_obtido": "Dados de abril",
        "status": "APROVADO",
        "executor": "QA Lima",
        "data_execucao": "2026-04-04",
        "evidencia": "Screenshot anexo",
    }
    return serialize_casos_teste_conteudo({"casos": [caso]}, RID)


def _deploy_completo() -> str:
    return serialize_deploy_conteudo(
        {
            "versao_entregue": "1.2.0",
            "ambiente": "produção",
            "data_deploy": "2026-04-05",
            "responsavel_deploy": "Ops Souza",
        },
        RID,
    )


@pytest.fixture
def mock_status_doc_atualizar():
    """
    POST /status usa validar_transicao em kanban_gates (doc via `services.kanban_gates.obter_documentacao_fases`).
    Status atual vem de `db.avaliacao_repo.obter_status_atual_requisito` (import local na validação).
    Persistência: `services.kanban_status_service.atualizar_status_requisito`.
    """
    with (
        patch("db.avaliacao_repo.obter_status_atual_requisito") as m_st,
        patch("services.kanban_gates.obter_documentacao_fases") as m_doc,
        patch("services.kanban_status_service.atualizar_status_requisito") as m_up,
    ):
        yield m_st, m_doc, m_up


def test_salvar_avaliacao_incremento_mock_repo():
    """Feature INCREMENTO: persistência delegada ao repo (sem DB real)."""
    body = {
        "id_requisito_ou_titulo": "Relatório de churn",
        "tipo_requisito": "INCREMENTO",
        "texto_original": "Quero relatório de churn por cohort.",
        "descricao_requisito": "Relatório exportável.",
        "objetivo": "Reduzir cancelamentos.",
        "finalidade": "Retenção.",
        "usuario_avaliador": "Tester",
        "respostas": [
            {"id_pergunta": 1, "texto": "Esforço?", "dimensao": "ESFORCO", "valor_resposta": 3},
            {"id_pergunta": 2, "texto": "Valor?", "dimensao": "VALOR", "valor_resposta": 4},
        ],
        "cadastro": {"id_projeto": 1},
    }
    with patch("services.avaliacao_service.salvar_avaliacao_completa") as m_save:
        m_save.return_value = {
            "sucesso": True,
            "id_entrada_bruta": 10,
            "id_requisito": RID,
            "id_avaliacao": 20,
        }
        r = client.post("/api/v1/requisitos/salvar-avaliacao", json=body)
    assert r.status_code == 200
    assert r.json()["id_requisito"] == RID
    m_save.assert_called_once()


def test_avanco_to_do_para_develop_bloqueado_sem_documentacao(mock_status_doc_atualizar):
    """Em TO DO (AVALIADO): não pode ir a DEVELOP sem prontidão (e doc) preenchidos."""
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "AVALIADO"
    m_doc.return_value = _fases_vazias()
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "EM_DESENVOLVIMENTO"})
    assert r.status_code == 422
    assert "Transição bloqueada" in r.json().get("detail", "")
    m_up.assert_not_called()


def test_avanco_com_doc_requisito_mas_sem_prontidao_ainda_bloqueado(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "AVALIADO"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "EM_DESENVOLVIMENTO"})
    assert r.status_code == 422
    assert "Transição bloqueada" in r.json()["detail"]
    m_up.assert_not_called()


def test_avanco_to_do_para_develop_permitido_com_doc_e_prontidao(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "AVALIADO"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    f["prontidao_dev"] = _prontidao_completa()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "EM_DESENVOLVIMENTO"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    m_up.assert_called_once()


def test_salto_duas_colunas_bloqueado(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "AVALIADO"
    m_doc.return_value = _fases_vazias()
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "EM_TESTE"})
    assert r.status_code == 422
    assert "uma coluna" in r.json()["detail"].lower() or "Salto" in r.json()["detail"]
    m_up.assert_not_called()


def test_retrocesso_develop_para_to_do_sem_doc_permitido(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "EM_DESENVOLVIMENTO"
    m_doc.return_value = _fases_vazias()
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "AVALIADO"})
    assert r.status_code == 200
    m_up.assert_called_once()


def test_backlog_para_to_do_bloqueado_sem_doc_requisito(mock_status_doc_atualizar):
    """BACKLOG → TO DO exige doc_requisito completo."""
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = None
    m_doc.return_value = _fases_vazias()
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "AVALIADO"})
    assert r.status_code == 422
    assert "Transição bloqueada" in r.json()["detail"]
    m_up.assert_not_called()


def test_backlog_para_to_do_permitido_com_doc_requisito(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = None
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "AVALIADO"})
    assert r.status_code == 200
    m_up.assert_called_once()


def test_develop_para_teste_bloqueado_sem_entrega_dev(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "EM_DESENVOLVIMENTO"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    f["prontidao_dev"] = _prontidao_completa()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "EM_TESTE"})
    assert r.status_code == 422
    assert "Transição bloqueada" in r.json()["detail"]
    m_up.assert_not_called()


def test_develop_para_teste_com_entrega_completa(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "EM_DESENVOLVIMENTO"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    f["prontidao_dev"] = _prontidao_completa()
    f["entrega_dev"] = _entrega_completa()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "EM_TESTE"})
    assert r.status_code == 200
    m_up.assert_called_once()


def test_teste_para_deploy_bloqueado_sem_caso_aprovado(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "EM_TESTE"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    f["prontidao_dev"] = _prontidao_completa()
    f["entrega_dev"] = _entrega_completa()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "DEPLOY"})
    assert r.status_code == 422
    m_up.assert_not_called()


def test_teste_para_deploy_com_caso_aprovado(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "EM_TESTE"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    f["prontidao_dev"] = _prontidao_completa()
    f["entrega_dev"] = _entrega_completa()
    f["casos_teste"] = _casos_teste_aprovado()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "DEPLOY"})
    assert r.status_code == 200
    m_up.assert_called_once()


def test_deploy_para_done_bloqueado_sem_deploy(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "DEPLOY"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    f["prontidao_dev"] = _prontidao_completa()
    f["entrega_dev"] = _entrega_completa()
    f["casos_teste"] = _casos_teste_aprovado()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "DONE"})
    assert r.status_code == 422
    m_up.assert_not_called()


def test_deploy_para_done_com_deploy_completo(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "DEPLOY"
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    f["prontidao_dev"] = _prontidao_completa()
    f["entrega_dev"] = _entrega_completa()
    f["casos_teste"] = _casos_teste_aprovado()
    f["deploy"] = _deploy_completo()
    m_doc.return_value = f
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "DONE"})
    assert r.status_code == 200
    m_up.assert_called_once()


def test_status_desconhecido_mapeia_para_backlog_retrocesso_permitido(mock_status_doc_atualizar):
    """Comportamento atual: status não mapeado vira coluna BACKLOG (retrocesso a partir de TO DO)."""
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "AVALIADO"
    m_doc.return_value = _fases_vazias()
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "FASE_INVENTADA"})
    assert r.status_code == 200
    m_up.assert_called_once()


def test_get_gates_indica_falta_documentacao():
    with (
        patch("services.kanban_status_service.obter_status_atual_requisito", return_value="AVALIADO"),
        patch("services.kanban_status_service.obter_documentacao_fases", return_value=_fases_vazias()),
    ):
        r = client.get(f"/api/v1/kanban/{RID}/gates")
    assert r.status_code == 200
    body = r.json()
    assert body["id_requisito"] == RID
    assert body["pode_avancar_documentacao"] is False
    assert isinstance(body["falta_documentacao"], list)
    assert len(body["falta_documentacao"]) > 0


def test_get_gates_com_doc_requisito_pode_avancar_para_proxima_etapa():
    f = _fases_vazias()
    f["doc_requisito"] = _doc_requisito_completo()
    with (
        patch("services.kanban_status_service.obter_status_atual_requisito", return_value="BACKLOG"),
        patch("services.kanban_status_service.obter_documentacao_fases", return_value=f),
    ):
        r = client.get(f"/api/v1/kanban/{RID}/gates")
    assert r.status_code == 200
    assert r.json()["pode_avancar_documentacao"] is True


def test_mesmo_status_nao_erro(mock_status_doc_atualizar):
    m_st, m_doc, m_up = mock_status_doc_atualizar
    m_st.return_value = "AVALIADO"
    m_doc.return_value = _fases_vazias()
    r = client.post(f"/api/v1/requisitos/{RID}/status", json={"status": "AVALIADO"})
    assert r.status_code == 200
    m_up.assert_called_once()
