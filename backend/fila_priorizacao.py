# -*- coding: utf-8 -*-
"""
Montagem da fila de priorização conforme calibragem (config_fila) e posição na matriz.

A fila é guiada pelas coordenadas (x, y), não pelo score_final.
Corte da matriz: CORTE_QUADRANTE = 2,5.

BUG (X = criticidade, Y = severidade):
  Q1 Crítica-alta:  x > 2,5 e y > 2,5
  Q2 Alta-média:    x > 2,5 e y <= 2,5
  Q3 Média:         x <= 2,5 e y > 2,5
  Q4 Baixa:         demais casos

INCREMENTO (X = esforço, Y = valor):
  Q1 Ganhos rápidos:     x <= 2,5 e y > 2,5
  Q2 Grandes projetos:   x > 2,5 e y > 2,5
  Q3 Melhorias simples:  x <= 2,5 e y <= 2,5
  Q4 Baixo retorno:      x > 2,5 e y <= 2,5

Ordenação (ambos os tipos):
  1) fila_ordem_quadrante ASC (estratégia do quadrante)
  2) fila_distancia_ideal ASC (distância ao canto ideal *daquele* quadrante)
  3) desempate por eixos conforme o quadrante (ver _desempate_*)
  4) dias_parado DESC
  5) id ASC

score_final = score_base — apenas referência (matriz / prioridade categórica).
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


FAIXA_LIMITES = [(0, 5, "Baixa"), (6, 11, "Média"), (12, 19, "Alta"), (20, 1e9, "Crítica")]

CORTE_QUADRANTE = 2.5

NOMES_QUADRANTE_BUG: dict[int, str] = {
    1: "Crítica-alta",
    2: "Alta-média",
    3: "Média",
    4: "Baixa",
}

NOMES_QUADRANTE_INCREMENTO: dict[int, str] = {
    1: "Ganhos rápidos",
    2: "Grandes projetos",
    3: "Melhorias simples",
    4: "Baixo retorno",
}

# Cantos ideais por quadrante (após classificar o item).
BUG_IDEAL_POR_QUADRANTE: dict[int, tuple[float, float]] = {
    1: (5.0, 5.0),           # máx. criticidade e severidade
    2: (5.0, CORTE_QUADRANTE),  # alta criticidade, maior severidade possível no Q2
    3: (CORTE_QUADRANTE, 5.0),  # maior severidade no Q3
    4: (CORTE_QUADRANTE, CORTE_QUADRANTE),  # menos desfavorável no Q4
}

INC_IDEAL_POR_QUADRANTE: dict[int, tuple[float, float]] = {
    1: (1.0, 5.0),              # Ganhos rápidos: baixo esforço, alto valor
    2: (CORTE_QUADRANTE, 5.0),  # Grandes projetos: maior valor, menor esforço na faixa
    3: (1.0, 1.0),              # Melhorias simples: menor esforço
    4: (CORTE_QUADRANTE, CORTE_QUADRANTE),  # Baixo retorno: menos pior dentro do Q4
}


def _dias_parado(data_avaliacao) -> float:
    """Dias desde a data de avaliação até hoje."""
    if not data_avaliacao:
        return 0.0
    if hasattr(data_avaliacao, "timestamp"):
        dt = data_avaliacao
    else:
        try:
            dt = datetime.fromisoformat(str(data_avaliacao).replace("Z", "+00:00"))
        except Exception:
            return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    agora = datetime.now(timezone.utc)
    delta = agora - dt
    return max(0.0, delta.total_seconds() / 86400.0)


def ordem_quadrante_bug(cx: float, cy: float) -> int:
    """1 = mais prioritário … 4 = menos. X=criticidade, Y=severidade."""
    x, y = float(cx), float(cy)
    t = CORTE_QUADRANTE
    if x > t and y > t:
        return 1
    if x > t and y <= t:
        return 2
    if x <= t and y > t:
        return 3
    return 4


def ordem_quadrante_incremento(cx: float, cy: float) -> int:
    """1 = ganhos rápidos … 4 = baixo retorno. X=esforço, Y=valor."""
    x, y = float(cx), float(cy)
    t = CORTE_QUADRANTE
    if x <= t and y > t:
        return 1
    if x > t and y > t:
        return 2
    if x <= t and y <= t:
        return 3
    return 4


def nome_quadrante(tipo: str, ordem: int) -> str:
    """Rótulo legível do quadrante para API/UI."""
    if (tipo or "").upper() == "BUG":
        return NOMES_QUADRANTE_BUG.get(ordem, "—")
    return NOMES_QUADRANTE_INCREMENTO.get(ordem, "—")


def canto_ideal_bug(ordem: int) -> tuple[float, float]:
    return BUG_IDEAL_POR_QUADRANTE.get(ordem, BUG_IDEAL_POR_QUADRANTE[4])


def canto_ideal_incremento(ordem: int) -> tuple[float, float]:
    return INC_IDEAL_POR_QUADRANTE.get(ordem, INC_IDEAL_POR_QUADRANTE[4])


def distancia_ao_canto(cx: float, cy: float, canto: tuple[float, float]) -> float:
    ix, iy = canto
    return math.hypot(float(cx) - ix, float(cy) - iy)


def distancia_ideal_bug(cx: float, cy: float, ordem: int | None = None) -> float:
    """Distância ao canto ideal do quadrante do bug."""
    if ordem is None:
        ordem = ordem_quadrante_bug(cx, cy)
    return distancia_ao_canto(cx, cy, canto_ideal_bug(ordem))


def distancia_ideal_incremento(cx: float, cy: float, ordem: int | None = None) -> float:
    """Distância ao canto ideal do quadrante do incremento."""
    if ordem is None:
        ordem = ordem_quadrante_incremento(cx, cy)
    return distancia_ao_canto(cx, cy, canto_ideal_incremento(ordem))


def _score_faixa(score_final: float) -> str:
    """Classificação visual: Baixa, Média, Alta, Crítica."""
    for min_s, max_s, nome in FAIXA_LIMITES:
        if min_s <= score_final <= max_s:
            return nome
    return "Baixa"


def _desempate_bug(item: dict) -> tuple:
    """Dentro do quadrante: maior severidade, depois maior criticidade."""
    return (
        -float(item.get("coordenada_y", 0.0)),
        -float(item.get("coordenada_x", 0.0)),
    )


def _desempate_incremento(item: dict) -> tuple:
    """
    Q1/Q2: maior valor, menor esforço.
    Q3/Q4: menor esforço, maior valor relativo.
    """
    ordem = int(item.get("fila_ordem_quadrante", 9))
    if ordem in (1, 2):
        return (
            -float(item.get("coordenada_y", 0.0)),
            float(item.get("coordenada_x", 0.0)),
        )
    return (
        float(item.get("coordenada_x", 0.0)),
        -float(item.get("coordenada_y", 0.0)),
    )


def _enriquecer_item(item: dict, _config: dict) -> None:
    """
    Preenche score_base, score_final, faixa, dias_parado, fila_ordem_quadrante,
    fila_quadrante_nome e fila_distancia_ideal (distância ao ideal do quadrante).
    """
    data_avaliacao = item.get("data_avaliacao")
    dias = _dias_parado(data_avaliacao)
    item["dias_parado"] = round(dias, 1)

    score_base = float(
        item.get("score")
        or (item.get("coordenada_x", 0) * item.get("coordenada_y", 0))
    )
    item["score_base"] = round(score_base, 2)

    tipo = (item.get("tipo_requisito") or "").upper()
    cx = float(item.get("coordenada_x", 0) or 0)
    cy = float(item.get("coordenada_y", 0) or 0)
    if tipo == "BUG":
        ordem = ordem_quadrante_bug(cx, cy)
        canto = canto_ideal_bug(ordem)
        item["fila_distancia_ideal"] = round(distancia_ideal_bug(cx, cy, ordem), 4)
    else:
        ordem = ordem_quadrante_incremento(cx, cy)
        canto = canto_ideal_incremento(ordem)
        item["fila_distancia_ideal"] = round(distancia_ideal_incremento(cx, cy, ordem), 4)

    item["fila_canto_ideal_x"] = round(canto[0], 2)
    item["fila_canto_ideal_y"] = round(canto[1], 2)
    item["fila_ordem_quadrante"] = ordem
    item["fila_quadrante_nome"] = nome_quadrante(tipo, ordem)

    score_final = score_base
    item["score_final"] = round(score_final, 2)
    item["faixa"] = _score_faixa(item["score_final"])


def chave_ordenacao_bug(item: dict) -> tuple:
    """Quadrante → distância ao ideal do quadrante → severidade → criticidade → dias → id."""
    return (
        int(item.get("fila_ordem_quadrante", 9)),
        float(item.get("fila_distancia_ideal", 1e9)),
        *_desempate_bug(item),
        -float(item.get("dias_parado", 0.0)),
        int(item.get("id", 0)),
    )


def chave_ordenacao_incremento(item: dict) -> tuple:
    """Quadrante → distância ao ideal do quadrante → desempate por Q → dias → id."""
    return (
        int(item.get("fila_ordem_quadrante", 9)),
        float(item.get("fila_distancia_ideal", 1e9)),
        *_desempate_incremento(item),
        -float(item.get("dias_parado", 0.0)),
        int(item.get("id", 0)),
    )


def chave_ordenacao_fila(item: dict) -> tuple:
    """Compatibilidade: delega ao tipo do item."""
    tipo = (item.get("tipo_requisito") or "").upper()
    if tipo == "BUG":
        return chave_ordenacao_bug(item)
    return chave_ordenacao_incremento(item)


def montar_duas_filas_completas(itens: list[dict], config: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """
    Todas as atividades BUG ordenadas entre si; todas INCREMENTO ordenadas entre si.
    Sem corte de vazão (para UI com duas filas separadas). Cada item é enriquecido in-place.
    """
    if not itens:
        return [], []
    for item in itens:
        _enriquecer_item(item, config)
    bugs = [i for i in itens if (i.get("tipo_requisito") or "").upper() == "BUG"]
    incrementos = [i for i in itens if (i.get("tipo_requisito") or "").upper() == "INCREMENTO"]
    bugs.sort(key=chave_ordenacao_bug)
    incrementos.sort(key=chave_ordenacao_incremento)
    return bugs, incrementos


def intercalar_por_vazao(
    bugs: list[dict],
    incrementos: list[dict],
    pct_bugs: float,
    pct_inc: float,
) -> list[dict]:
    """
    Intercala duas filas já ordenadas respeitando a proporção configurada (ex.: 2/98).
    Usa comparação (i+1)/peso_bugs vs (j+1)/peso_inc para distribuir ao longo da lista.
    """
    if not bugs:
        return list(incrementos)
    if not incrementos:
        return list(bugs)
    peso_bugs = max(float(pct_bugs), 0.01)
    peso_inc = max(float(pct_inc), 0.01)
    fila: list[dict] = []
    i_b = i_i = 0
    while i_b < len(bugs) or i_i < len(incrementos):
        if i_b >= len(bugs):
            fila.append(incrementos[i_i])
            i_i += 1
        elif i_i >= len(incrementos):
            fila.append(bugs[i_b])
            i_b += 1
        elif (i_b + 1) / peso_bugs <= (i_i + 1) / peso_inc:
            fila.append(bugs[i_b])
            i_b += 1
        else:
            fila.append(incrementos[i_i])
            i_i += 1
    return fila


def montar_fila(
    itens: list[dict],
    config: dict[str, Any],
    tamanho: int | None = None,
    intercalar: bool = True,
) -> list[dict]:
    """
    Enriquece itens, ordena por quadrante e desempates por tipo; monta fila com vazão.
    """
    if not itens:
        return []
    vazao = config.get("vazao") or {}
    pct_bugs = float(vazao.get("bugs", 60))
    pct_inc = float(vazao.get("incrementos", 40))
    pct_bugs_frac = pct_bugs / 100.0
    pct_inc_frac = pct_inc / 100.0

    for item in itens:
        _enriquecer_item(item, config)

    bugs = [i for i in itens if (i.get("tipo_requisito") or "").upper() == "BUG"]
    incrementos = [i for i in itens if (i.get("tipo_requisito") or "").upper() == "INCREMENTO"]

    bugs.sort(key=chave_ordenacao_bug)
    incrementos.sort(key=chave_ordenacao_incremento)

    tamanho = tamanho or len(itens)
    lista_completa = tamanho >= len(itens)

    if lista_completa:
        n_bugs = len(bugs)
        n_inc = len(incrementos)
    else:
        n_bugs = min(max(0, int(round(tamanho * pct_bugs_frac))), len(bugs))
        n_inc = min(max(0, int(round(tamanho * pct_inc_frac))), len(incrementos))
        if n_bugs + n_inc > tamanho:
            excesso = n_bugs + n_inc - tamanho
            if n_inc >= excesso:
                n_inc -= excesso
            else:
                excesso -= n_inc
                n_inc = 0
                n_bugs = max(0, n_bugs - excesso)

    top_bugs = bugs[:n_bugs]
    top_inc = incrementos[:n_inc]

    if not intercalar:
        return top_bugs + top_inc

    fila = intercalar_por_vazao(top_bugs, top_inc, pct_bugs, pct_inc)
    if not lista_completa and len(fila) > tamanho:
        fila = fila[:tamanho]
    return fila
