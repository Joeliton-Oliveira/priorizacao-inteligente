# -*- coding: utf-8 -*-
"""Transição de status no Kanban e cálculo de gates documentais."""
from __future__ import annotations

from typing import Any

from domain.exceptions import ValidacaoDominioError
from db.avaliacao_repo import (
    atualizar_status_requisito,
    obter_status_atual_requisito,
    obter_tipo_requisito,
)
from db.doc_fase_repo import obter_documentacao_fases
from services.kanban_gates import (
    KANBAN_NEXT,
    contar_ocupacao_coluna_kanban,
    gate_documental_para_avancar_de_coluna,
    obter_limite_wip_coluna,
    status_api_para_coluna_kanban,
    validar_transicao_status_kanban,
    validar_wip_coluna_destino,
)


def atualizar_status_atividade(id_requisito: int, status: str) -> None:
    ok, err = validar_transicao_status_kanban(id_requisito, status)
    if not ok:
        raise ValidacaoDominioError(err or "Transição não permitida.")
    atualizar_status_requisito(id_requisito, status)


def _wip_destino_payload(coluna_destino: str | None, id_requisito: int) -> dict[str, Any] | None:
    if not coluna_destino:
        return None
    limite = obter_limite_wip_coluna(coluna_destino)
    if limite is None:
        return None
    ocupacao = contar_ocupacao_coluna_kanban(coluna_destino, excluir_id_requisito=id_requisito)
    return {"coluna": coluna_destino, "ocupacao": ocupacao, "limite": limite}


def obter_gates_kanban(id_requisito: int) -> dict[str, Any]:
    st_raw = obter_status_atual_requisito(id_requisito)
    st_norm = (st_raw or "BACKLOG").strip()
    col = status_api_para_coluna_kanban(st_norm)
    tipo_requisito = obter_tipo_requisito(id_requisito)
    fases = obter_documentacao_fases(id_requisito)
    prox = KANBAN_NEXT.get(col) if col != "DONE" else None
    gate_ok, falta = (True, [])
    if prox:
        gate_ok, falta = gate_documental_para_avancar_de_coluna(col, fases, tipo_requisito)

    pode_avancar_wip = True
    wip_destino = _wip_destino_payload(prox, id_requisito)
    if prox and wip_destino:
        try:
            idx_cur = ["BACKLOG", "TO DO", "DEVELOP", "TEST", "DEPLOY", "DONE"].index(col)
            idx_dest = ["BACKLOG", "TO DO", "DEVELOP", "TEST", "DEPLOY", "DONE"].index(prox)
        except ValueError:
            idx_cur = idx_dest = 0
        wip_ok, _wip_err, wip_destino = validar_wip_coluna_destino(prox, id_requisito, idx_dest, idx_cur)
        pode_avancar_wip = wip_ok
        if wip_destino is None:
            wip_destino = _wip_destino_payload(prox, id_requisito)

    return {
        "id_requisito": id_requisito,
        "status_atual": st_norm,
        "coluna_kanban": col,
        "proxima_coluna": prox,
        "pode_avancar_documentacao": gate_ok,
        "pode_avancar_wip": pode_avancar_wip,
        "wip_destino": wip_destino,
        "falta_documentacao": falta,
    }
