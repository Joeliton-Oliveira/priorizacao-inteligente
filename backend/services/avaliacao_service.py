# -*- coding: utf-8 -*-
"""Casos de uso: listagem de atividades priorizadas e persistência de avaliação completa."""
from __future__ import annotations

from typing import Any, Optional

from domain.exceptions import RecursoNaoEncontradoError, ValidacaoDominioError
from db.avaliacao_repo import listar_atividades_priorizadas, salvar_avaliacao_completa


def listar_atividades_matriz() -> list[dict[str, Any]]:
    return listar_atividades_priorizadas()


def salvar_avaliacao(
    texto_original: str,
    titulo_requisito: str,
    descricao_requisito: str,
    tipo_requisito: str,
    objetivo: str,
    finalidade: str,
    usuario_avaliador: str,
    perfil_avaliador: Optional[str],
    respostas: list[dict[str, Any]],
    cadastro: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    try:
        return salvar_avaliacao_completa(
            texto_original=texto_original,
            titulo_requisito=titulo_requisito,
            descricao_requisito=descricao_requisito,
            tipo_requisito=tipo_requisito,
            objetivo=objetivo,
            finalidade=finalidade,
            usuario_avaliador=usuario_avaliador,
            perfil_avaliador=perfil_avaliador,
            respostas=respostas,
            cadastro=cadastro,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "Projeto não encontrado.":
            raise RecursoNaoEncontradoError("Projeto não encontrado") from e
        raise ValidacaoDominioError(msg) from e
