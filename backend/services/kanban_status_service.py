# -*- coding: utf-8 -*-
"""Transição de status no Kanban e cálculo de gates documentais."""
from __future__ import annotations

from typing import Any

from domain.exceptions import ValidacaoDominioError
from db.avaliacao_repo import atualizar_status_requisito, obter_status_atual_requisito
from db.doc_fase_repo import obter_documentacao_fases
from services.kanban_gates import (
    KANBAN_NEXT,
    gate_documental_para_avancar_de_coluna,
    status_api_para_coluna_kanban,
    validar_transicao_status_kanban,
)


def atualizar_status_atividade(id_requisito: int, status: str) -> None:
    ok, err = validar_transicao_status_kanban(id_requisito, status)
    if not ok:
        raise ValidacaoDominioError(err or "Transição não permitida.")
    atualizar_status_requisito(id_requisito, status)


def obter_gates_kanban(id_requisito: int) -> dict[str, Any]:
    st_raw = obter_status_atual_requisito(id_requisito)
    st_norm = (st_raw or "BACKLOG").strip()
    col = status_api_para_coluna_kanban(st_norm)
    fases = obter_documentacao_fases(id_requisito)
    prox = KANBAN_NEXT.get(col) if col != "DONE" else None
    gate_ok, falta = (True, [])
    if prox:
        gate_ok, falta = gate_documental_para_avancar_de_coluna(col, fases)
    return {
        "id_requisito": id_requisito,
        "status_atual": st_norm,
        "coluna_kanban": col,
        "proxima_coluna": prox,
        "pode_avancar_documentacao": gate_ok,
        "falta_documentacao": falta,
    }
