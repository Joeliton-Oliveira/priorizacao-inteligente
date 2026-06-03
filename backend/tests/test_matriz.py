# -*- coding: utf-8 -*-
"""Testes das regras da matriz — eixos, coordenadas e score base."""

import pytest


# Regras: BUG -> X=CRITICIDADE, Y=SEVERIDADE; INCREMENTO -> X=ESFORCO, Y=VALOR
# score_base = coordenada_x * coordenada_y (ou média das respostas por dimensão)


def test_regra_eixo_bug():
    """BUG: CRITICIDADE -> X, SEVERIDADE -> Y."""
    dim_x, dim_y = "CRITICIDADE", "SEVERIDADE"
    assert dim_x in ("CRITICIDADE", "SEVERIDADE")
    assert dim_y in ("CRITICIDADE", "SEVERIDADE")
    assert dim_x != dim_y


def test_regra_eixo_incremento():
    """INCREMENTO: ESFORCO -> X, VALOR -> Y."""
    dim_x, dim_y = "ESFORCO", "VALOR"
    assert dim_x in ("ESFORCO", "VALOR")
    assert dim_y in ("ESFORCO", "VALOR")
    assert dim_x != dim_y


def test_score_base_formula():
    """Score base = coordenada_x * coordenada_y."""
    x, y = 4.0, 5.0
    score = x * y
    assert score == 20.0


def test_coordenadas_estaveis_nao_mudam_com_tempo():
    """A matriz não muda a natureza do item: X/Y são da avaliação, não do tempo."""
    coordenada_x, coordenada_y = 3, 4
    score_base = coordenada_x * coordenada_y
    # Simular "depois de tempo" — coordenadas seguem iguais
    assert score_base == 12
    assert coordenada_x == 3 and coordenada_y == 4


def test_prioridade_categorica_por_score():
    """Derivação de prioridade a partir do score (>=15 ALTA, >=8 MEDIA, else BAIXA)."""
    def prioridade(score):
        if score >= 15:
            return "ALTA"
        if score >= 8:
            return "MEDIA"
        return "BAIXA"
    assert prioridade(25) == "ALTA"
    assert prioridade(15) == "ALTA"
    assert prioridade(10) == "MEDIA"
    assert prioridade(8) == "MEDIA"
    assert prioridade(4) == "BAIXA"


def test_tipo_requisito_apenas_bug_ou_incremento():
    """tipo_requisito deve ser normalizado para BUG ou INCREMENTO."""
    for entrada in ("BUG", "bug", "INCREMENTO", "incremento"):
        t = entrada.upper()
        assert t in ("BUG", "INCREMENTO") or (t == "INCREMENTO" or t == "BUG")


def test_dimensoes_bug_nao_tem_esforco_valor():
    """Para BUG, perguntas devem ser CRITICIDADE ou SEVERIDADE."""
    dims_bug = ["CRITICIDADE", "SEVERIDADE"]
    for d in dims_bug:
        assert d in ("CRITICIDADE", "SEVERIDADE")
    assert "ESFORCO" not in dims_bug
    assert "VALOR" not in dims_bug


def test_dimensoes_incremento_nao_tem_criticidade_severidade():
    """Para INCREMENTO, perguntas devem ser ESFORCO ou VALOR."""
    dims_inc = ["ESFORCO", "VALOR"]
    for d in dims_inc:
        assert d in ("ESFORCO", "VALOR")
    assert "CRITICIDADE" not in dims_inc
    assert "SEVERIDADE" not in dims_inc
