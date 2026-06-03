# -*- coding: utf-8 -*-
"""
Exceções de domínio com código HTTP sugerido para o controller.
O FastAPI mapeia via `exception_handler(DomainError)`.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base: subclasses definem `status_http` para resposta JSON."""

    status_http: int = 500

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RecursoNaoEncontradoError(DomainError):
    status_http = 404


class ValidacaoDominioError(DomainError):
    status_http = 422


class EntradaInvalidaErro(DomainError):
    status_http = 400


class AnaliseIaErro(DomainError):
    """Falha na resposta da IA ou formato inválido."""

    status_http = 502
