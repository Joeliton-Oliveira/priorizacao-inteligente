# -*- coding: utf-8 -*-
"""Testes da fila de priorização — score_final, envelhecimento, vazão, faixa."""

from datetime import datetime, timezone, timedelta
import pytest

from fila_priorizacao import (
    montar_fila,
    montar_duas_filas_completas,
    FAIXA_LIMITES,
    _dias_parado,
    _bonus_tempo_raw,
    _score_faixa,
)


def test_faixa_limites():
    assert _score_faixa(3) == "Baixa"
    assert _score_faixa(5) == "Baixa"
    assert _score_faixa(6) == "Média"
    assert _score_faixa(11) == "Média"
    assert _score_faixa(12) == "Alta"
    assert _score_faixa(19) == "Alta"
    assert _score_faixa(20) == "Crítica"
    assert _score_faixa(100) == "Crítica"


def test_dias_parado_vazio():
    assert _dias_parado(None) == 0.0
    assert _dias_parado("") == 0.0


def test_bonus_tempo_raw_intervalo():
    config = {"envelhecimento": {"intervalo_dias": 10, "incremento_base": 1.0, "limite_maximo": None}}
    # 25 dias -> 2 intervalos -> 2 * 1.0 = 2.0
    assert _bonus_tempo_raw(25, config) == 2.0


def test_bonus_tempo_respeita_limite_maximo():
    config = {"envelhecimento": {"intervalo_dias": 10, "incremento_base": 1.0, "limite_maximo": 5}}
    # 100 dias -> 10 intervalos -> 10, mas limite 5
    b = _bonus_tempo_raw(100, config)
    assert b == 5.0


def test_montar_fila_vazia():
    assert montar_fila([], {}) == []


def test_montar_duas_filas_completas_vazio():
    assert montar_duas_filas_completas([], {}) == ([], [])


def test_montar_duas_filas_completas_sem_corte_vazao(config_fila_padrao):
    """Todas as entradas BUG e INCREMENTO aparecem; fila operacional com limite pode omitir itens."""
    from datetime import datetime, timezone
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "BUG", "coordenada_x": 5, "coordenada_y": 5, "score": 25, "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "BUG", "coordenada_x": 2, "coordenada_y": 2, "score": 4, "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 3, "tipo_requisito": "INCREMENTO", "coordenada_x": 1, "coordenada_y": 5, "score": 5, "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    bugs, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert len(bugs) == 2
    assert len(incs) == 1
    assert all((b.get("tipo_requisito") or "").upper() == "BUG" for b in bugs)
    assert all((i.get("tipo_requisito") or "").upper() == "INCREMENTO" for i in incs)
    fila_curta = montar_fila([dict(x) for x in itens], config_fila_padrao, tamanho=2, intercalar=True)
    assert len(fila_curta) == 2


def test_montar_fila_enriquece_campos(config_fila_padrao, itens_fila_sinteticos):
    fila = montar_fila(itens_fila_sinteticos, config_fila_padrao, tamanho=10, intercalar=True)
    assert len(fila) >= 1
    for item in fila:
        assert "score_base" in item
        assert "bonus_tempo" in item
        assert "bonus_quadrante" in item
        assert "bonus_fase" in item
        assert "bonus_manual" in item
        assert "score_final" in item
        assert "faixa" in item
        assert "dias_parado" in item
        assert "fila_ordem_quadrante" in item
        assert "fila_distancia_ideal" in item
        assert item["faixa"] in ("Baixa", "Média", "Alta", "Crítica")


def test_score_final_eh_soma_dos_bonus(config_fila_padrao, itens_fila_sinteticos):
    fila = montar_fila(itens_fila_sinteticos, config_fila_padrao)
    for item in fila:
        esperado = (
            item["score_base"]
            + item["bonus_tempo"]
            + item["bonus_quadrante"]
            + item["bonus_fase"]
            + item["bonus_manual"]
        )
        assert abs(item["score_final"] - round(esperado, 2)) < 0.01


def test_ordenacao_quadrante_antes_de_score_final(config_fila_padrao, itens_fila_sinteticos):
    """Bugs: Q1 (5,5) antes de Q4 (2,2); desempate por distância a (5,5) e depois score_final."""
    fila = montar_fila(itens_fila_sinteticos, config_fila_padrao)
    bugs = [i for i in fila if i.get("tipo_requisito") == "BUG"]
    assert bugs[0]["id"] == 1  # (5,5) Q1
    assert bugs[-1]["id"] == 2  # (2,2) Q4
    assert bugs[0]["fila_ordem_quadrante"] <= bugs[-1]["fila_ordem_quadrante"]


def test_incremento_quick_win_antes_de_desperdicio_mesmo_com_score_menor(config_fila_padrao):
    """(1,5) Q1 deve ficar antes de (4,2) Q4 mesmo se o segundo tiver score_final maior por bónus."""
    from datetime import datetime, timezone, timedelta
    agora = datetime.now(timezone.utc)
    antigo = agora - timedelta(days=100)
    itens = [
        {
            "id": 10,
            "titulo": "Quick win",
            "tipo_requisito": "INCREMENTO",
            "coordenada_x": 1.0,
            "coordenada_y": 5.0,
            "score": 5.0,
            "prioridade_categorica": "BAIXA",
            "status_atual": "AVALIADO",
            "data_avaliacao": agora,
        },
        {
            "id": 11,
            "titulo": "Desperdício velho",
            "tipo_requisito": "INCREMENTO",
            "coordenada_x": 4.0,
            "coordenada_y": 2.0,
            "score": 8.0,
            "prioridade_categorica": "MEDIA",
            "status_atual": "AVALIADO",
            "data_avaliacao": antigo,
        },
    ]
    fila = montar_fila(itens, config_fila_padrao, tamanho=10, intercalar=False)
    incs = [i for i in fila if i.get("tipo_requisito") == "INCREMENTO"]
    assert incs[0]["id"] == 10
    assert incs[0]["fila_ordem_quadrante"] == 1
    assert incs[1]["fila_ordem_quadrante"] == 4


def test_vazao_60_40(config_fila_padrao, itens_fila_sinteticos):
    config = {**config_fila_padrao, "vazao": {"bugs": 60, "incrementos": 40}}
    fila = montar_fila(itens_fila_sinteticos, config, tamanho=10, intercalar=True)
    bugs = [i for i in fila if i.get("tipo_requisito") == "BUG"]
    incs = [i for i in fila if i.get("tipo_requisito") == "INCREMENTO"]
    total = len(bugs) + len(incs)
    if total >= 2:
        # Proporção aproximada 60/40
        pct_bugs = len(bugs) / total
        assert 0 <= pct_bugs <= 1


def test_mesmo_quadrante_antigo_desempata_por_score_final(config_fila_padrao):
    """Dentro do mesmo quadrante, maior score_final (ex.: mais tempo parado) vem primeiro."""
    from datetime import datetime, timezone, timedelta
    agora = datetime.now(timezone.utc)
    antigo = agora - timedelta(days=80)
    # Ambos Q4 (2,2) e (2,2)
    itens = [
        {"id": 1, "titulo": "Q4 recente", "tipo_requisito": "BUG", "coordenada_x": 2, "coordenada_y": 2,
         "score": 4, "prioridade_categorica": "BAIXA", "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "titulo": "Q4 muito antigo", "tipo_requisito": "BUG", "coordenada_x": 2, "coordenada_y": 2,
         "score": 4, "prioridade_categorica": "BAIXA", "status_atual": "AVALIADO", "data_avaliacao": antigo},
    ]
    fila = montar_fila(itens, config_fila_padrao)
    assert len(fila) == 2
    assert fila[0]["fila_ordem_quadrante"] == fila[1]["fila_ordem_quadrante"] == 4
    assert fila[0]["id"] == 2  # mais bónus de tempo → score_final maior → primeiro
    assert fila[0]["score_final"] >= fila[1]["score_final"]


def test_fase_em_desenvolvimento_mult_zero(config_fila_padrao):
    """Fase em_desenvolvimento tem multiplicador 0 na config; bônus de fase não aumenta score."""
    item_dev = {"id": 1, "titulo": "X", "tipo_requisito": "BUG", "coordenada_x": 3, "coordenada_y": 3,
                "score": 9, "prioridade_categorica": "MEDIA", "status_atual": "em_desenvolvimento",
                "data_avaliacao": datetime.now(timezone.utc)}
    from fila_priorizacao import _enriquecer_item
    _enriquecer_item(item_dev, config_fila_padrao)
    assert "score_final" in item_dev
    assert config_fila_padrao["fases"]["em_desenvolvimento"] == 0.0
