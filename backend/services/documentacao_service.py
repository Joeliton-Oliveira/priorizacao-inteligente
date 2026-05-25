# -*- coding: utf-8 -*-
"""Documentação por fase (evidências Kanban)."""
from __future__ import annotations

from typing import Any

from domain.exceptions import ValidacaoDominioError
from db.doc_fase_repo import (
    FASES_DOC_VALIDAS,
    obter_documentacao_fases,
    salvar_documentacao_fase as repo_salvar_documentacao_fase,
)

__all__ = ["FASES_DOC_VALIDAS", "listar_documentacao_fases", "gravar_documentacao_fase"]


def listar_documentacao_fases(id_requisito: int) -> dict[str, Any]:
    return obter_documentacao_fases(id_requisito)


def gravar_documentacao_fase(id_requisito: int, fase_codigo: str, conteudo: str) -> Any:
    try:
        return repo_salvar_documentacao_fase(id_requisito, fase_codigo, conteudo)
    except ValueError as e:
        raise ValidacaoDominioError(str(e)) from e
