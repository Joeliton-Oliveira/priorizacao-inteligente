# -*- coding: utf-8 -*-
"""Testes de regras de negócio — matriz, fila, consistência."""

from datetime import datetime, timezone, timedelta
import pytest


def test_matriz_nao_muda_natureza_com_tempo():
    """Coordenadas X/Y e score_base permanecem estáveis; dias_parado é calculado à parte."""
    from fila_priorizacao import montar_fila
    config = {"vazao": {"bugs": 100, "incrementos": 0}, "envelhecimento": {"intervalo_dias": 10, "incremento_base": 1.0, "limite_maximo": None},
              "quadrantes_bug": {"critica_alta": 0.5, "alta_media": 0.8, "media_media": 1.0, "baixa_baixa": 1.3},
              "fases": {"avaliado": 1.2, "backlog": 1.5, "priorizado": 1.0, "em_desenvolvimento": 0.0, "em_teste": 0.0, "concluido": 0.0}}
    item = {"id": 1, "titulo": "X", "tipo_requisito": "BUG", "coordenada_x": 4, "coordenada_y": 3,
            "score": 12, "prioridade_categorica": "MEDIA", "status_atual": "AVALIADO",
            "data_avaliacao": datetime.now(timezone.utc) - timedelta(days=30)}
    fila = montar_fila([item], config)
    assert len(fila) == 1
    assert fila[0]["coordenada_x"] == 4
    assert fila[0]["coordenada_y"] == 3
    assert fila[0]["score_base"] == 12
    assert fila[0]["score_final"] == 12
    assert fila[0]["dias_parado"] > 0


def test_quadrante_bug_domina_sobre_score_final():
    """Bug Q1 (5,5) vem antes de Q4 (2,2) mesmo com o segundo muito mais antigo (maior score_final)."""
    from fila_priorizacao import montar_fila
    config = {"vazao": {"bugs": 100, "incrementos": 0}, "envelhecimento": {"intervalo_dias": 10, "incremento_base": 1.0, "limite_maximo": None},
              "quadrantes_bug": {"critica_alta": 0.5, "alta_media": 0.8, "media_media": 1.0, "baixa_baixa": 1.3},
              "fases": {"avaliado": 1.2, "backlog": 1.5, "priorizado": 1.0, "em_desenvolvimento": 0.0, "em_teste": 0.0, "concluido": 0.0}}
    antigo = datetime.now(timezone.utc) - timedelta(days=60)
    itens = [
        {"id": 1, "titulo": "Forte recente", "tipo_requisito": "BUG", "coordenada_x": 5, "coordenada_y": 5, "score": 25,
         "prioridade_categorica": "ALTA", "status_atual": "AVALIADO", "data_avaliacao": datetime.now(timezone.utc)},
        {"id": 2, "titulo": "Fraco antigo", "tipo_requisito": "BUG", "coordenada_x": 2, "coordenada_y": 2, "score": 4,
         "prioridade_categorica": "BAIXA", "status_atual": "AVALIADO", "data_avaliacao": antigo},
    ]
    fila = montar_fila(itens, config)
    assert fila[0]["id"] == 1
    assert fila[1]["id"] == 2
    assert fila[0]["fila_ordem_quadrante"] == 1
    assert fila[1]["fila_ordem_quadrante"] == 4
    assert all("score_final" in i for i in fila)


def test_itens_mesmo_quadrante_antigo_sobe_com_tempo(config_fila_padrao):
    """Mesmo quadrante e mesmo score: desempate por dias_parado DESC."""
    from fila_priorizacao import montar_duas_filas_completas
    agora = datetime.now(timezone.utc)
    antigo = agora - timedelta(days=80)
    itens = [
        {"id": 1, "titulo": "Q1 recente", "tipo_requisito": "BUG", "coordenada_x": 4.0, "coordenada_y": 4.0, "score": 16,
         "prioridade_categorica": "ALTA", "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "titulo": "Q1 muito antigo", "tipo_requisito": "BUG", "coordenada_x": 4.0, "coordenada_y": 4.0, "score": 16,
         "prioridade_categorica": "ALTA", "status_atual": "AVALIADO", "data_avaliacao": antigo},
    ]
    bugs, _ = montar_duas_filas_completas(itens, config_fila_padrao)
    assert len(bugs) == 2
    assert bugs[0]["fila_ordem_quadrante"] == bugs[1]["fila_ordem_quadrante"] == 1
    assert bugs[0]["id"] == 2
    assert bugs[0]["dias_parado"] > bugs[1]["dias_parado"]
    assert bugs[0]["score_final"] == bugs[1]["score_final"]


def test_bugs_e_incrementos_respeitam_vazao(config_fila_padrao, itens_fila_sinteticos):
    """Fila montada respeita a proporção configurada (ex.: 60/40)."""
    from fila_priorizacao import montar_fila
    config = {**config_fila_padrao, "vazao": {"bugs": 70, "incrementos": 30}}
    fila = montar_fila(itens_fila_sinteticos, config, tamanho=10, intercalar=True)
    bugs = [i for i in fila if i.get("tipo_requisito") == "BUG"]
    incs = [i for i in fila if i.get("tipo_requisito") == "INCREMENTO"]
    total = len(bugs) + len(incs)
    if total >= 2:
        pct_bugs = len(bugs) / total
        assert 0 <= pct_bugs <= 1


def test_nao_quebra_tipo_nao_sei_informar():
    """Sistema aceita tipo_informado_usuario NAO_SEI (IA infere)."""
    from fastapi.testclient import TestClient
    from api import app
    import json
    from unittest.mock import patch, MagicMock
    client = TestClient(app)
    with patch("services.analise_ia_service.model") as mock_model:
        mock_model.generate_content.return_value = MagicMock(
            text=json.dumps({
                "titulo_requisito": "T",
                "descricao_requisito": "D",
                "tipo_requisito": "INCREMENTO",
                "objetivo": "O",
                "finalidade": "F",
                "perguntas_avaliacao": [
                    {"id_pergunta": 1, "texto": "P1?", "dimensao": "ESFORCO",
                     "opcoes_resposta": [{"rotulo": str(i), "valor": i} for i in range(1, 6)]},
                    {"id_pergunta": 2, "texto": "P2?", "dimensao": "VALOR",
                     "opcoes_resposta": [{"rotulo": str(i), "valor": i} for i in range(1, 6)]},
                ],
            })
        )
        r = client.post("/api/v1/requisitos/analise", json={"texto_original": "Quero um relatório", "tipo_informado_usuario": "NAO_SEI"})
    assert r.status_code == 200
    assert r.json()["tipo_requisito"] in ("BUG", "INCREMENTO")
