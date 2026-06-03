# -*- coding: utf-8 -*-
"""Testes do módulo de prompts — contexto e montagem do prompt para a IA."""
import pytest
from prompts import CONTEXTO_SISTEMA, montar_prompt_analise


def test_contexto_sistema_contem_regras_bug_incremento():
    assert "BUG" in CONTEXTO_SISTEMA
    assert "INCREMENTO" in CONTEXTO_SISTEMA
    assert "CRITICIDADE" in CONTEXTO_SISTEMA or "Severidade" in CONTEXTO_SISTEMA
    assert "ESFORCO" in CONTEXTO_SISTEMA or "VALOR" in CONTEXTO_SISTEMA


def test_contexto_exige_5_opcoes_likert():
    assert "5" in CONTEXTO_SISTEMA or "cinco" in CONTEXTO_SISTEMA.lower() or "Likert" in CONTEXTO_SISTEMA


def test_montar_prompt_payload_minimo():
    payload = {"texto_original": "Botão não funciona"}
    prompt = montar_prompt_analise(payload)
    assert "Botão não funciona" in prompt
    assert "titulo_requisito" in prompt or "JSON" in prompt


def test_montar_prompt_inclui_contexto_enriquecido():
    payload = {
        "texto_original": "Problema no checkout",
        "tipo_informado_usuario": "BUG",
        "modulo_afetado": "checkout",
        "objetivo_desejado": "Finalizar compra",
    }
    prompt = montar_prompt_analise(payload)
    assert "Problema no checkout" in prompt
    assert "BUG" in prompt
    assert "checkout" in prompt
    assert "Finalizar compra" in prompt


def test_montar_prompt_exige_json():
    prompt = montar_prompt_analise({"texto_original": "x"})
    assert "JSON" in prompt or "json" in prompt


def test_montar_prompt_dimensoes_bug():
    prompt = montar_prompt_analise({"texto_original": "bug"})
    assert "CRITICIDADE" in prompt or "SEVERIDADE" in prompt or "dimensao" in prompt.lower()
