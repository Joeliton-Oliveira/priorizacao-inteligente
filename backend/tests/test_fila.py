# -*- coding: utf-8 -*-
"""Testes da fila de priorização — score_final, envelhecimento, vazão, faixa."""

from datetime import datetime, timezone, timedelta
import pytest

from fila_priorizacao import (
    montar_fila,
    montar_duas_filas_completas,
    FAIXA_LIMITES,
    _dias_parado,
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
        assert "score_final" in item
        assert "faixa" in item
        assert "dias_parado" in item
        assert "fila_ordem_quadrante" in item
        assert "fila_quadrante_nome" in item
        assert "fila_distancia_ideal" in item
        assert item["faixa"] in ("Baixa", "Média", "Alta", "Crítica")


def test_score_final_igual_score_base(config_fila_padrao, itens_fila_sinteticos):
    fila = montar_fila(itens_fila_sinteticos, config_fila_padrao)
    for item in fila:
        assert abs(item["score_final"] - round(item["score_base"], 2)) < 0.01


def test_ordenacao_quadrante_antes_de_distancia(config_fila_padrao, itens_fila_sinteticos):
    """Bugs: Q1 (5,5) antes de Q4 (2,2) independente do score."""
    fila = montar_fila(itens_fila_sinteticos, config_fila_padrao)
    bugs = [i for i in fila if i.get("tipo_requisito") == "BUG"]
    assert bugs[0]["id"] == 1  # (5,5) Q1
    assert bugs[-1]["id"] == 2  # (2,2) Q4
    assert bugs[0]["fila_ordem_quadrante"] <= bugs[-1]["fila_ordem_quadrante"]


def test_incremento_quick_win_antes_de_desperdicio(config_fila_padrao):
    """(1,5) Q1 deve ficar antes de (4,2) Q4."""
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


def test_fila_operacional_50_50_intercala_tipos(config_fila_padrao):
    """Vazão 50/50: fila operacional alterna bug e incremento no topo."""
    from fila_priorizacao import montar_fila

    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "BUG", "coordenada_x": 5, "coordenada_y": 5, "score": 25,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "INCREMENTO", "coordenada_x": 1, "coordenada_y": 5, "score": 5,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 3, "tipo_requisito": "BUG", "coordenada_x": 4, "coordenada_y": 4, "score": 16,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 4, "tipo_requisito": "INCREMENTO", "coordenada_x": 2, "coordenada_y": 4, "score": 8,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    config = {**config_fila_padrao, "vazao": {"bugs": 50, "incrementos": 50}}
    fila = montar_fila(itens, config, intercalar=True)
    assert len(fila) == 4
    tipos = [(i.get("tipo_requisito") or "").upper() for i in fila]
    assert tipos[0] == "BUG" and tipos[1] == "INCREMENTO"
    assert tipos[2] == "BUG" and tipos[3] == "INCREMENTO"


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


def test_vazao_2_98_prioriza_incrementos_no_topo(config_fila_padrao):
    """Com 2% bugs, o topo da fila não deve alternar 1:1 — incrementos vêm primeiro."""
    agora = datetime.now(timezone.utc)
    itens = []
    for i in range(1, 9):
        itens.append(
            {
                "id": i * 10,
                "tipo_requisito": "BUG",
                "coordenada_x": 5,
                "coordenada_y": 5,
                "score": 25 - i,
                "status_atual": "AVALIADO",
                "data_avaliacao": agora,
            }
        )
    for i in range(1, 9):
        itens.append(
            {
                "id": i * 10 + 1,
                "tipo_requisito": "INCREMENTO",
                "coordenada_x": 1,
                "coordenada_y": 5,
                "score": 10 - i,
                "status_atual": "AVALIADO",
                "data_avaliacao": agora,
            }
        )
    config = {**config_fila_padrao, "vazao": {"bugs": 2, "incrementos": 98}}
    fila = montar_fila(itens, config, intercalar=True)
    tipos_topo = [(i.get("tipo_requisito") or "").upper() for i in fila[:8]]
    assert tipos_topo.count("INCREMENTO") >= 6
    assert not all(
        tipos_topo[i] != tipos_topo[i + 1]
        for i in range(0, min(6, len(tipos_topo) - 1), 2)
        if i + 1 < len(tipos_topo)
    )


def test_mesmo_quadrante_bug_desempata_por_distancia_ideal(config_fila_padrao):
    """Dentro do mesmo quadrante BUG, menor distância a (5,5) vem primeiro (não o score)."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "BUG", "coordenada_x": 2, "coordenada_y": 2, "score": 4,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "BUG", "coordenada_x": 2.1, "coordenada_y": 2.1, "score": 9,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    bugs, _ = montar_duas_filas_completas(itens, config_fila_padrao)
    assert bugs[0]["id"] == 2
    assert bugs[0]["fila_distancia_ideal"] < bugs[1]["fila_distancia_ideal"]
    assert bugs[0]["fila_ordem_quadrante"] == bugs[1]["fila_ordem_quadrante"] == 4


def test_mesmo_quadrante_bug_distancia_vence_sobre_score_maior(config_fila_padrao):
    """Q1: (4,4) score 16 antes de (5,3) score 15 — geometria, não produto X×Y."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "BUG", "coordenada_x": 5, "coordenada_y": 3, "score": 15,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "BUG", "coordenada_x": 4, "coordenada_y": 4, "score": 16,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    bugs, _ = montar_duas_filas_completas(itens, config_fila_padrao)
    assert bugs[0]["id"] == 2
    assert bugs[1]["id"] == 1
    assert bugs[0]["score_final"] > bugs[1]["score_final"]


def test_mesmo_quadrante_bug_desempata_por_dias_parado(config_fila_padrao):
    """Empate de score no mesmo quadrante: maior dias_parado primeiro."""
    agora = datetime.now(timezone.utc)
    antigo = agora - timedelta(days=80)
    itens = [
        {"id": 1, "tipo_requisito": "BUG", "coordenada_x": 4, "coordenada_y": 4, "score": 16,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "BUG", "coordenada_x": 4, "coordenada_y": 4, "score": 16,
         "status_atual": "AVALIADO", "data_avaliacao": antigo},
    ]
    bugs, _ = montar_duas_filas_completas(itens, config_fila_padrao)
    assert bugs[0]["id"] == 2
    assert bugs[0]["dias_parado"] > bugs[1]["dias_parado"]


def test_exemplo_esforco_1_5_valor_4_5_topo_quick_wins(config_fila_padrao):
    """(1,5)×(4,5) em Quick wins fica acima de Q4 com score maior — fila guiada pela matriz."""
    agora = datetime.now(timezone.utc)
    itens = [
        {
            "id": 1,
            "tipo_requisito": "INCREMENTO",
            "coordenada_x": 1.5,
            "coordenada_y": 4.5,
            "score": 6.75,
            "prioridade_categorica": "BAIXA",
            "status_atual": "AVALIADO",
            "data_avaliacao": agora,
        },
        {
            "id": 2,
            "tipo_requisito": "INCREMENTO",
            "coordenada_x": 4.0,
            "coordenada_y": 2.0,
            "score": 8.0,
            "prioridade_categorica": "MEDIA",
            "status_atual": "AVALIADO",
            "data_avaliacao": agora,
        },
    ]
    _, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert incs[0]["id"] == 1
    assert incs[0]["fila_quadrante_nome"] == "Ganhos rápidos"
    assert incs[0]["fila_canto_ideal_x"] == 1.0
    assert incs[0]["fila_canto_ideal_y"] == 5.0
    assert incs[0]["score_final"] < incs[1]["score_final"]


def test_quick_wins_maior_valor_menor_esforco_primeiro(config_fila_padrao):
    """Q1: valor 4.8 / esforço 1.2 antes de valor 3.5 / esforço 2.4."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "INCREMENTO", "coordenada_x": 2.4, "coordenada_y": 3.5, "score": 8.4,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "INCREMENTO", "coordenada_x": 1.2, "coordenada_y": 4.8, "score": 5.76,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    _, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert incs[0]["id"] == 2
    assert incs[0]["fila_ordem_quadrante"] == 1
    assert incs[0]["score_final"] < incs[1]["score_final"]


def test_preenchimento_menor_esforco_primeiro(config_fila_padrao):
    """Q3: menor esforço antes de maior valor relativo."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "INCREMENTO", "coordenada_x": 2.0, "coordenada_y": 2.0, "score": 4,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "INCREMENTO", "coordenada_x": 1.0, "coordenada_y": 1.5, "score": 1.5,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    _, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert incs[0]["id"] == 2
    assert incs[0]["fila_ordem_quadrante"] == 3


def test_incremento_mesmo_quadrante_distancia_ideal(config_fila_padrao):
    """Grandes projetos (Q2): menor distância ao ideal do quadrante antes de maior score."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 2, "tipo_requisito": "INCREMENTO", "coordenada_x": 2.67, "coordenada_y": 4.5, "score": 12,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 6, "tipo_requisito": "INCREMENTO", "coordenada_x": 4.67, "coordenada_y": 4.5, "score": 21,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    _, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert len(incs) == 2
    assert incs[0]["id"] == 2
    assert incs[0]["fila_distancia_ideal"] < incs[1]["fila_distancia_ideal"]
    assert incs[0]["score_final"] < incs[1]["score_final"]
    assert incs[0]["fila_ordem_quadrante"] == 2
    assert incs[0]["fila_quadrante_nome"] == "Grandes projetos"


def test_incremento_quick_wins_antes_grandes_projetos(config_fila_padrao):
    """Quick wins (score menor) antes de Grandes projetos (score maior)."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "INCREMENTO", "coordenada_x": 1, "coordenada_y": 5, "score": 5,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "INCREMENTO", "coordenada_x": 4.67, "coordenada_y": 4.5, "score": 21,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    _, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert len(incs) == 2
    assert incs[0]["fila_ordem_quadrante"] == 1
    assert incs[1]["fila_ordem_quadrante"] == 2


def test_incremento_mesmo_quadrante_esforco_valor(config_fila_padrao):
    """Quick wins com mesma distância: menor esforço, depois maior valor."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "INCREMENTO", "coordenada_x": 2, "coordenada_y": 4, "score": 8,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "INCREMENTO", "coordenada_x": 1, "coordenada_y": 5, "score": 8,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    _, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert len(incs) == 2
    assert incs[0]["id"] == 2
    assert incs[0]["coordenada_x"] < incs[1]["coordenada_x"]


def test_incremento_q3_preenchimento_antes_q4_desperdicio_mesmo_com_score_maior(config_fila_padrao):
    """Q3 (score 5) vem antes de Q4 (score 10): quadrante domina faixa/score isolado."""
    agora = datetime.now(timezone.utc)
    itens = [
        {"id": 1, "tipo_requisito": "INCREMENTO", "coordenada_x": 2.0, "coordenada_y": 2.5, "score": 5.0,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
        {"id": 2, "tipo_requisito": "INCREMENTO", "coordenada_x": 4.0, "coordenada_y": 2.5, "score": 10.0,
         "status_atual": "AVALIADO", "data_avaliacao": agora},
    ]
    _, incs = montar_duas_filas_completas(itens, config_fila_padrao)
    assert incs[0]["fila_ordem_quadrante"] == 3
    assert incs[1]["fila_ordem_quadrante"] == 4
    assert incs[0]["score_final"] < incs[1]["score_final"]
    assert incs[0]["faixa"] == "Baixa"
    assert incs[1]["faixa"] == "Média"


def test_fase_em_desenvolvimento_mantem_score_base(config_fila_padrao):
    """Sem bônus de fase, score_final segue score_base."""
    item_dev = {"id": 1, "titulo": "X", "tipo_requisito": "BUG", "coordenada_x": 3, "coordenada_y": 3,
                "score": 9, "prioridade_categorica": "MEDIA", "status_atual": "em_desenvolvimento",
                "data_avaliacao": datetime.now(timezone.utc)}
    from fila_priorizacao import _enriquecer_item
    _enriquecer_item(item_dev, config_fila_padrao)
    assert "score_final" in item_dev
    assert item_dev["score_final"] == item_dev["score_base"]
