# -*- coding: utf-8 -*-
"""Tipos e erros de domínio (sem FastAPI)."""

from domain.exceptions import (
    AnaliseIaErro,
    DomainError,
    EntradaInvalidaErro,
    RecursoNaoEncontradoError,
    ValidacaoDominioError,
)

__all__ = [
    "AnaliseIaErro",
    "DomainError",
    "EntradaInvalidaErro",
    "RecursoNaoEncontradoError",
    "ValidacaoDominioError",
]
