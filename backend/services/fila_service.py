# -*- coding: utf-8 -*-
"""
Casos de uso da fila de priorização (operacional e duas filas).
Orquestra config_fila, listagem de atividades e fila_priorizacao.
"""
from __future__ import annotations

from typing import Any, Optional

from config_fila import get_config_fila
from db.avaliacao_repo import listar_atividades_para_fila
from fila_priorizacao import montar_duas_filas_completas, montar_fila


def serialize_fila_item(item: dict) -> dict:
    c = dict(item)
    if c.get("data_avaliacao") and hasattr(c["data_avaliacao"], "isoformat"):
        c["data_avaliacao"] = c["data_avaliacao"].isoformat()
    return c


def obter_fila_priorizacao(
    limite: Optional[int] = None,
    intercalar: bool = True,
) -> list[dict[str, Any]]:
    config = get_config_fila()
    itens = listar_atividades_para_fila()
    fila = montar_fila(itens, config, tamanho=limite, intercalar=intercalar)
    return [serialize_fila_item(item) for item in fila]


def obter_fila_bugs() -> list[dict[str, Any]]:
    config = get_config_fila()
    itens = listar_atividades_para_fila()
    bugs, _ = montar_duas_filas_completas(itens, config)
    return [serialize_fila_item(x) for x in bugs]


def obter_fila_incrementos() -> list[dict[str, Any]]:
    config = get_config_fila()
    itens = listar_atividades_para_fila()
    _, incrementos = montar_duas_filas_completas(itens, config)
    return [serialize_fila_item(x) for x in incrementos]
