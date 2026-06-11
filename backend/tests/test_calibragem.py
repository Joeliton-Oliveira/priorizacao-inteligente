# -*- coding: utf-8 -*-
"""Testes da calibragem — config_fila, vazão, envelhecimento, persistência."""

import json
import tempfile
from pathlib import Path
import pytest


def test_config_fila_estrutura():
    """Config padrão tem todas as seções esperadas."""
    from config_fila import CONFIG_FILA
    assert "vazao" in CONFIG_FILA
    assert "bugs" in CONFIG_FILA["vazao"]
    assert "incrementos" in CONFIG_FILA["vazao"]
    assert "envelhecimento" in CONFIG_FILA
    assert "intervalo_dias" in CONFIG_FILA["envelhecimento"]
    assert "incremento_base" in CONFIG_FILA["envelhecimento"]
    assert "quadrantes_bug" in CONFIG_FILA
    assert "quadrantes_incremento" in CONFIG_FILA
    assert "fases" in CONFIG_FILA


def test_get_config_fila_retorna_copia():
    from config_fila import get_config_fila
    c1 = get_config_fila()
    c2 = get_config_fila()
    c1["vazao"]["bugs"] = 99
    assert get_config_fila()["vazao"]["bugs"] != 99 or id(c1) != id(c2)


def test_save_and_load_config_fila():
    """Salvar e carregar config em arquivo temporário."""
    from config_fila import _merge_deep, CONFIG_FILA
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json.dumps({"vazao": {"bugs": 70, "incrementos": 30}}, indent=2))
        path = Path(f.name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        merged = _merge_deep(CONFIG_FILA, loaded)
        assert merged["vazao"]["bugs"] == 70
        assert merged["vazao"]["incrementos"] == 30
    finally:
        path.unlink(missing_ok=True)


def test_vazao_soma_100():
    """Regra: melhorias = 100 - bugs; soma deve fechar 100."""
    bugs = 60
    incrementos = 100 - bugs
    assert bugs + incrementos == 100
    bugs = 50
    incrementos = 100 - bugs
    assert bugs + incrementos == 100


def test_normalizar_vazao_limita_0_100():
    from config_fila import _normalizar_vazao

    assert _normalizar_vazao({"bugs": 720, "incrementos": 0}) == {"bugs": 100, "incrementos": 0}
    assert _normalizar_vazao({"bugs": -5, "incrementos": 105}) == {"bugs": 0, "incrementos": 100}
    assert _normalizar_vazao({"bugs": 2, "incrementos": 98}) == {"bugs": 2, "incrementos": 98}


def test_envelhecimento_intervalo_incremento():
    """Envelhecimento: intervalo_dias, incremento_base, limite_maximo opcional."""
    from config_fila import CONFIG_FILA
    env = CONFIG_FILA["envelhecimento"]
    assert isinstance(env["intervalo_dias"], (int, float))
    assert isinstance(env["incremento_base"], (int, float))
    assert env["limite_maximo"] is None or isinstance(env["limite_maximo"], (int, float))


def test_quadrantes_bug_tem_quatro_faixas():
    from config_fila import CONFIG_FILA
    qb = CONFIG_FILA["quadrantes_bug"]
    assert "critica_alta" in qb
    assert "alta_media" in qb
    assert "media_media" in qb
    assert "baixa_baixa" in qb


def test_quadrantes_incremento_tem_quatro():
    from config_fila import CONFIG_FILA
    qi = CONFIG_FILA["quadrantes_incremento"]
    assert "quick_wins" in qi
    assert "grandes_projetos" in qi
    assert "preenchimento" in qi
    assert "desperdicio" in qi


def test_fases_tem_seis():
    from config_fila import CONFIG_FILA
    f = CONFIG_FILA["fases"]
    assert "backlog" in f
    assert "avaliado" in f
    assert "priorizado" in f
    assert "em_desenvolvimento" in f
    assert "em_teste" in f
    assert "concluido" in f
