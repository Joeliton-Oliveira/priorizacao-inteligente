# -*- coding: utf-8 -*-
"""
Casos de uso de projetos (cadastro, listagem, status, versão, histórico).
Camada de serviço: orquestra db/projeto_repo sem conhecimento de HTTP.
"""
from __future__ import annotations

from typing import Any, Optional

from domain.exceptions import RecursoNaoEncontradoError, ValidacaoDominioError
from db.projeto_repo import (
    atualizar_status_projeto as repo_atualizar_status_projeto,
    criar_projeto as repo_criar_projeto,
    evoluir_versao_projeto as repo_evoluir_projeto,
    listar_historico_versao_projeto as repo_listar_historico_projeto,
    listar_projetos as repo_listar_projetos,
)


def criar_projeto(
    nome_projeto: str,
    tipo_origem: str,
    descricao: Optional[str] = None,
    responsavel: Optional[str] = None,
    versao_atual_informada: Optional[str] = None,
    status_projeto: str = "ativo",
) -> dict[str, Any]:
    try:
        return repo_criar_projeto(
            nome_projeto=nome_projeto.strip(),
            tipo_origem=tipo_origem,
            descricao=descricao,
            responsavel=responsavel,
            versao_atual_informada=versao_atual_informada,
            status_projeto=status_projeto,
        )
    except ValueError as e:
        raise ValidacaoDominioError(str(e)) from e


def listar_projetos(
    tipo_origem: Optional[str] = None,
    status: Optional[str] = None,
    busca_nome: Optional[str] = None,
) -> list[dict[str, Any]]:
    t = (tipo_origem or "").strip().lower()
    if t and t not in ("novo", "existente"):
        raise ValidacaoDominioError("tipo_origem deve ser 'novo', 'existente' ou vazio (todos).")
    st = (status or "").strip().lower()
    if st and st not in ("ativo", "arquivado", "descontinuado"):
        raise ValidacaoDominioError("status deve ser 'ativo', 'arquivado', 'descontinuado' ou vazio (todos).")
    try:
        return repo_listar_projetos(
            tipo_origem=t if t in ("novo", "existente") else None,
            status_projeto=st if st in ("ativo", "arquivado", "descontinuado") else None,
            busca_nome=(busca_nome or "").strip() or None,
        )
    except ValueError as e:
        raise ValidacaoDominioError(str(e)) from e


def atualizar_status_projeto(id_projeto: int, status: str) -> dict[str, Any]:
    try:
        return repo_atualizar_status_projeto(id_projeto, status)
    except LookupError:
        raise RecursoNaoEncontradoError("Projeto não encontrado") from None
    except ValueError as e:
        raise ValidacaoDominioError(str(e)) from e


def evoluir_versao_projeto(
    id_projeto: int,
    nivel: str,
    motivo: Optional[str] = None,
    usuario_responsavel: Optional[str] = None,
) -> dict[str, Any]:
    try:
        return repo_evoluir_projeto(
            id_projeto,
            nivel,
            motivo=motivo,
            usuario_responsavel=usuario_responsavel,
        )
    except LookupError:
        raise RecursoNaoEncontradoError("Projeto não encontrado") from None
    except ValueError as e:
        raise ValidacaoDominioError(str(e)) from e


def listar_historico_versao(id_projeto: int, limite: int = 100) -> list[dict[str, Any]]:
    return repo_listar_historico_projeto(id_projeto, limite=limite)
