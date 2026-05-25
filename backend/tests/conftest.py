# -*- coding: utf-8 -*-
"""Fixtures compartilhadas para a suíte de testes."""
import os

# Garantir diretório temporário utilizável (evita FileNotFoundError quando /tmp etc. não existem)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_pytest_tmp = os.path.join(_root, ".pytest_tmp")
os.makedirs(_pytest_tmp, exist_ok=True)
os.environ["TMPDIR"] = _pytest_tmp
os.environ["TEMP"] = _pytest_tmp
os.environ["TMP"] = _pytest_tmp

import json
import pytest


# Resposta JSON mínima que a IA deve retornar (usado em mocks)
RESPOSTA_IA_BUG = {
    "titulo_requisito": "Botão de finalizar compra não responde",
    "descricao_requisito": "Problema no checkout.",
    "tipo_requisito": "BUG",
    "objetivo": "Corrigir o botão.",
    "finalidade": "Permitir conclusão da compra.",
    "perguntas_avaliacao": [
        {
            "id_pergunta": 1,
            "texto": "Qual a criticidade?",
            "dimensao": "CRITICIDADE",
            "opcoes_resposta": [
                {"rotulo": "Muito baixo", "valor": 1},
                {"rotulo": "Baixo", "valor": 2},
                {"rotulo": "Médio", "valor": 3},
                {"rotulo": "Alto", "valor": 4},
                {"rotulo": "Muito alto", "valor": 5},
            ],
        },
        {
            "id_pergunta": 2,
            "texto": "Qual a severidade?",
            "dimensao": "SEVERIDADE",
            "opcoes_resposta": [
                {"rotulo": "Muito baixo", "valor": 1},
                {"rotulo": "Baixo", "valor": 2},
                {"rotulo": "Médio", "valor": 3},
                {"rotulo": "Alto", "valor": 4},
                {"rotulo": "Muito alto", "valor": 5},
            ],
        },
    ],
}

RESPOSTA_IA_INCREMENTO = {
    "titulo_requisito": "Dashboard comercial",
    "descricao_requisito": "Nova tela de indicadores.",
    "tipo_requisito": "INCREMENTO",
    "objetivo": "Visão gerencial.",
    "finalidade": "Apoiar decisões.",
    "perguntas_avaliacao": [
        {
            "id_pergunta": 1,
            "texto": "Esforço estimado?",
            "dimensao": "ESFORCO",
            "opcoes_resposta": [
                {"rotulo": "Muito baixo", "valor": 1},
                {"rotulo": "Baixo", "valor": 2},
                {"rotulo": "Médio", "valor": 3},
                {"rotulo": "Alto", "valor": 4},
                {"rotulo": "Muito alto", "valor": 5},
            ],
        },
        {
            "id_pergunta": 2,
            "texto": "Valor para o negócio?",
            "dimensao": "VALOR",
            "opcoes_resposta": [
                {"rotulo": "Muito baixo", "valor": 1},
                {"rotulo": "Baixo", "valor": 2},
                {"rotulo": "Médio", "valor": 3},
                {"rotulo": "Alto", "valor": 4},
                {"rotulo": "Muito alto", "valor": 5},
            ],
        },
    ],
}


@pytest.fixture
def payload_analise_minimo():
    """Payload mínimo para estruturação com IA (só texto)."""
    return {"texto_original": "O botão de finalizar compra não funciona."}


@pytest.fixture
def payload_analise_enriquecido():
    """Payload com contexto enriquecido."""
    return {
        "texto_original": "O botão de finalizar compra não responde no checkout.",
        "tipo_informado_usuario": "BUG",
        "modulo_afetado": "checkout",
        "contexto_negocio": "Vendas online",
        "objetivo_desejado": "Cliente deve conseguir finalizar a compra.",
    }


@pytest.fixture
def config_fila_padrao():
    """Config da fila para testes (vazão, envelhecimento, quadrantes, fases)."""
    return {
        "vazao": {"bugs": 60, "incrementos": 40},
        "envelhecimento": {
            "intervalo_dias": 10,
            "incremento_base": 1.0,
            "limite_maximo": None,
        },
        "quadrantes_incremento": {
            "quick_wins": 1.4,
            "grandes_projetos": 1.0,
            "preenchimento": 1.3,
            "desperdicio": 0.7,
        },
        "quadrantes_bug": {
            "critica_alta": 0.5,
            "alta_media": 0.8,
            "media_media": 1.0,
            "baixa_baixa": 1.3,
        },
        "fases": {
            "backlog": 1.5,
            "avaliado": 1.2,
            "priorizado": 1.0,
            "em_desenvolvimento": 0.0,
            "em_teste": 0.0,
            "concluido": 0.0,
        },
    }


@pytest.fixture
def itens_fila_sinteticos():
    """Itens sintéticos para testar montar_fila (sem DB)."""
    from datetime import datetime, timezone, timedelta
    agora = datetime.now(timezone.utc)
    antigo = agora - timedelta(days=60)
    return [
        {
            "id": 1,
            "titulo": "Bug crítico",
            "tipo_requisito": "BUG",
            "coordenada_x": 5,
            "coordenada_y": 5,
            "score": 25,
            "prioridade_categorica": "ALTA",
            "status_atual": "AVALIADO",
            "data_avaliacao": agora,
        },
        {
            "id": 2,
            "titulo": "Bug antigo fraco",
            "tipo_requisito": "BUG",
            "coordenada_x": 2,
            "coordenada_y": 2,
            "score": 4,
            "prioridade_categorica": "BAIXA",
            "status_atual": "AVALIADO",
            "data_avaliacao": antigo,
        },
        {
            "id": 3,
            "titulo": "Incremento",
            "tipo_requisito": "INCREMENTO",
            "coordenada_x": 4,
            "coordenada_y": 2,
            "score": 8,
            "prioridade_categorica": "MEDIA",
            "status_atual": "AVALIADO",
            "data_avaliacao": antigo,
        },
    ]
