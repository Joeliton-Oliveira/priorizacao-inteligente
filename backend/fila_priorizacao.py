# -*- coding: utf-8 -*-
"""
Montagem da fila de priorização conforme calibragem (config_fila) e regras de quadrante/vazão (ver README.md).

Ordenação dentro de cada tipo (BUG vs INCREMENTO):
1) Quadrante com corte em 2,5 (prioridade Q1 → Q4 conforme o documento).
2) Distância ao canto ideal da matriz (bugs → (5,5); incrementos → (1,5)).
3) Desempate: score_final DESC (mantém efeito de tempo, fase e multiplicadores).

BUG:   X=criticidade, Y=severidade. Q1 (x>2,5 e y>2,5) mais prioritário.
INC:   X=esforço, Y=valor. Q1 (x≤2,5 e y>2,5) quick wins, mais prioritário.

Fórmula score_final (camada B, explicativa e desempate):
  score_final = score_base + bonus_tempo + bonus_quadrante + bonus_fase + bonus_manual
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


# Faixas do score_final para classificação visual (baixa / média / alta / crítica)
FAIXA_LIMITES = [(0, 5, "Baixa"), (6, 11, "Média"), (12, 19, "Alta"), (20, 1e9, "Crítica")]

# Bugs: criticidade×severidade, quadrantes com corte 2,5; incrementos: esforço×valor (quick wins).
CORTE_QUADRANTE = 2.5
BUG_CANTO_IDEAL = (5.0, 5.0)  # criticidade × severidade — priorizar proximidade
INC_CANTO_IDEAL = (1.0, 5.0)  # esforço × valor — baixo esforço, alto valor


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


def _bonus_tempo_raw(dias_parado: float, config: dict) -> float:
    """Bônus bruto por tempo parado (antes de multiplicadores)."""
    env = config.get("envelhecimento") or {}
    intervalo = env.get("intervalo_dias") or 10
    incremento = env.get("incremento_base") or 1.0
    limite = env.get("limite_maximo")
    bonus = (dias_parado // intervalo) * incremento
    if limite is not None:
        bonus = min(bonus, float(limite))
    return bonus


def _multiplicador_fase(status: str, config: dict) -> float:
    fases = config.get("fases") or {}
    k = (status or "avaliado").lower().replace(" ", "_")
    return float(fases.get(k, fases.get("avaliado", 1.0)))


def ordem_quadrante_bug(cx: float, cy: float) -> int:
    """1 = mais prioritário … 4 = menos (corte CORTE_QUADRANTE). X=criticidade, Y=severidade."""
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
    """1 = quick wins … 4 = desperdício. X=esforço, Y=valor."""
    x, y = float(cx), float(cy)
    t = CORTE_QUADRANTE
    if x <= t and y > t:
        return 1
    if x > t and y > t:
        return 2
    if x <= t and y <= t:
        return 3
    return 4


def distancia_ideal_bug(cx: float, cy: float) -> float:
    """Distância euclidiana a BUG_CANTO_IDEAL (quanto menor, mais urgente)."""
    ix, iy = BUG_CANTO_IDEAL
    return math.hypot(ix - float(cx), iy - float(cy))


def distancia_ideal_incremento(cx: float, cy: float) -> float:
    """Distância euclidiana a INC_CANTO_IDEAL (quanto menor, melhor o quick win)."""
    ix, iy = INC_CANTO_IDEAL
    return math.hypot(float(cx) - ix, iy - float(cy))


def _multiplicador_quadrante_bug_coords(cx: float, cy: float, config: dict) -> float:
    """Multiplicador de envelhecimento conforme quadrante real (coordenadas), não prioridade_categorica."""
    qb = config.get("quadrantes_bug") or {}
    q = ordem_quadrante_bug(cx, cy)
    if q == 1:
        return float(qb.get("critica_alta", qb.get("alta_media", 1.0)))
    if q == 2:
        return float(qb.get("alta_media", 0.8))
    if q == 3:
        return float(qb.get("media_media", 1.0))
    return float(qb.get("baixa_baixa", 1.3))


def _multiplicador_quadrante_incremento_coords(cx: float, cy: float, config: dict) -> float:
    qi = config.get("quadrantes_incremento") or {}
    q = ordem_quadrante_incremento(cx, cy)
    if q == 1:
        return float(qi.get("quick_wins", 1.4))
    if q == 2:
        return float(qi.get("grandes_projetos", 1.0))
    if q == 3:
        return float(qi.get("preenchimento", 1.3))
    return float(qi.get("desperdicio", 0.7))


def _score_faixa(score_final: float) -> str:
    """Classificação visual: Baixa, Média, Alta, Crítica."""
    for min_s, max_s, nome in FAIXA_LIMITES:
        if min_s <= score_final <= max_s:
            return nome
    return "Baixa"


def _enriquecer_item(item: dict, config: dict) -> None:
    """
    Preenche no item os campos do número principal (camada B):
    score_base, bonus_tempo, bonus_quadrante, bonus_fase, bonus_manual,
    score_final, faixa, dias_parado.
    A ordenação da fila usa apenas score_final.
    """
    data_avaliacao = item.get("data_avaliacao")
    dias = _dias_parado(data_avaliacao)
    item["dias_parado"] = round(dias, 1)

    # Score base (matriz)
    score_base = float(
        item.get("score")
        or (item.get("coordenada_x", 0) * item.get("coordenada_y", 0))
    )
    item["score_base"] = round(score_base, 2)

    # Bônus tempo (bruto)
    bonus_tempo = _bonus_tempo_raw(dias, config)
    item["bonus_tempo"] = round(bonus_tempo, 2)

    # Multiplicadores
    fase_mult = _multiplicador_fase(item.get("status_atual", "avaliado"), config)
    tipo = (item.get("tipo_requisito") or "").upper()
    cx = float(item.get("coordenada_x", 0) or 0)
    cy = float(item.get("coordenada_y", 0) or 0)
    if tipo == "BUG":
        quad_mult = _multiplicador_quadrante_bug_coords(cx, cy, config)
        item["fila_ordem_quadrante"] = ordem_quadrante_bug(cx, cy)
        item["fila_distancia_ideal"] = round(distancia_ideal_bug(cx, cy), 4)
    else:
        quad_mult = _multiplicador_quadrante_incremento_coords(cx, cy, config)
        item["fila_ordem_quadrante"] = ordem_quadrante_incremento(cx, cy)
        item["fila_distancia_ideal"] = round(distancia_ideal_incremento(cx, cy), 4)

    # Decomposição aditiva: bonus_quadrante e bonus_fase são o "extra" dos multiplicadores
    # total_ajuste = bonus_tempo * quad_mult * fase_mult
    # bonus_quadrante = bonus_tempo * (quad_mult - 1), bonus_fase = bonus_tempo * quad_mult * (fase_mult - 1)
    bonus_quadrante = bonus_tempo * (quad_mult - 1.0)
    bonus_fase = bonus_tempo * quad_mult * (fase_mult - 1.0)
    item["bonus_quadrante"] = round(bonus_quadrante, 2)
    item["bonus_fase"] = round(bonus_fase, 2)
    item["bonus_manual"] = 0.0

    # Número principal: score_final ordena a fila
    score_final = score_base + bonus_tempo + bonus_quadrante + bonus_fase + item["bonus_manual"]
    item["score_final"] = round(score_final, 2)
    item["faixa"] = _score_faixa(item["score_final"])


def chave_ordenacao_fila(item: dict) -> tuple:
    """Tuplo para ordenar: quadrante (1 primeiro), distância ao canto ideal, score_final (desempate)."""
    return (
        int(item.get("fila_ordem_quadrante", 9)),
        float(item.get("fila_distancia_ideal", 1e9)),
        -float(item.get("score_final", 0.0)),
    )


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
    bugs.sort(key=chave_ordenacao_fila)
    incrementos.sort(key=chave_ordenacao_fila)
    return bugs, incrementos


def montar_fila(
    itens: list[dict],
    config: dict[str, Any],
    tamanho: int | None = None,
    intercalar: bool = True,
) -> list[dict]:
    """
    Enriquece cada item com score_base, bônus e score_final; ordena por score_final DESC;
    monta a fila respeitando a vazão (bugs % / melhorias %).
    Retorna lista de itens com campos da camada B preenchidos.
    """
    if not itens:
        return []
    vazao = config.get("vazao") or {}
    pct_bugs = float(vazao.get("bugs", 60)) / 100.0
    pct_inc = float(vazao.get("incrementos", 40)) / 100.0

    for item in itens:
        _enriquecer_item(item, config)

    bugs = [i for i in itens if (i.get("tipo_requisito") or "").upper() == "BUG"]
    incrementos = [i for i in itens if (i.get("tipo_requisito") or "").upper() == "INCREMENTO"]

    bugs.sort(key=chave_ordenacao_fila)
    incrementos.sort(key=chave_ordenacao_fila)

    tamanho = tamanho or len(itens)
    n_bugs = max(0, int(round(tamanho * pct_bugs)))
    n_inc = max(0, min(tamanho - n_bugs, len(incrementos)))
    n_bugs = min(n_bugs, len(bugs))
    if n_bugs + n_inc < tamanho and n_bugs < len(bugs):
        n_bugs = min(tamanho - n_inc, len(bugs))
    elif n_bugs + n_inc < tamanho and n_inc < len(incrementos):
        n_inc = min(tamanho - n_bugs, len(incrementos))

    top_bugs = bugs[:n_bugs]
    top_inc = incrementos[:n_inc]

    if not intercalar:
        return top_bugs + top_inc

    fila = []
    i_b, i_i = 0, 0
    while i_b < len(top_bugs) or i_i < len(top_inc):
        if i_b < len(top_bugs):
            fila.append(top_bugs[i_b])
            i_b += 1
        if i_i < len(top_inc):
            fila.append(top_inc[i_i])
            i_i += 1
    return fila
