# -*- coding: utf-8 -*-
"""Regras de gate para BACKLOG em BUG x FEATURE."""

from db.doc_fase_repo import serialize_doc_requisito_completo, serialize_prontidao_dev_conteudo
from services.kanban_gates import (
    eval_fase_docs_doc_requisito_gate,
    eval_fase_docs_prontidao_gate,
    gate_documental_para_avancar_de_coluna,
)


def test_backlog_gate_bug_nao_exige_regras_e_criterios():
    raw = serialize_doc_requisito_completo(
        {
            "nome_funcionalidade": "Corrigir timeout",
            "descricao_detalhada": "Erro ao consultar API externa.",
            "restricoes": "Nenhuma",
        },
        ["A consulta deve retornar sem timeout."],
        ["Tempo de resposta menor que 2s."],
        regras=[],
        criterios=[],
    )

    ok, falta = eval_fase_docs_doc_requisito_gate(
        raw,
        exigir_regras_e_criterios=False,
    )

    assert ok is True
    assert falta == []


def test_backlog_gate_feature_exige_regras_e_criterios():
    raw = serialize_doc_requisito_completo(
        {
            "nome_funcionalidade": "Nova tela de dashboard",
            "descricao_detalhada": "Adicionar visão consolidada.",
            "restricoes": "Nenhuma",
        },
        ["Exibir cartões de resumo."],
        ["Carregar em até 3s."],
        regras=[],
        criterios=[],
    )

    ok, falta = eval_fase_docs_doc_requisito_gate(
        raw,
        exigir_regras_e_criterios=True,
    )

    assert ok is False
    assert "Pelo menos uma regra de negócio" in falta
    assert "Pelo menos um critério de aceitação" in falta


def test_backlog_coluna_bug_dispensa_doc_requisito_vazio():
    ok, falta = gate_documental_para_avancar_de_coluna(
        "BACKLOG",
        {"doc_requisito": ""},
        "BUG",
    )
    assert ok is True
    assert falta == []


def test_backlog_coluna_incremento_exige_doc_requisito():
    ok, falta = gate_documental_para_avancar_de_coluna(
        "BACKLOG",
        {"doc_requisito": ""},
        "INCREMENTO",
    )
    assert ok is False
    assert len(falta) > 0


def test_prontidao_gate_bug_dispensa_criterios_existem_no_checklist():
    raw = serialize_prontidao_dev_conteudo(
        {
            "responsavel_desenvolvimento": "Dev",
            "registrado_por": "PO",
            "data_prontidao": "2026-06-02",
            "observacoes_tecnicas": "",
            "checklist": [
                "documento_revisado",
                "escopo_entendido",
                "responsavel_definido",
            ],
        },
        1,
    )
    ok, falta = eval_fase_docs_prontidao_gate(
        raw,
        {"doc_requisito": ""},
        tipo_requisito="BUG",
    )
    assert ok is True
    assert falta == []
