# -*- coding: utf-8 -*-
"""Casos de uso da calibragem da fila (leitura e persistência)."""
from __future__ import annotations

from typing import Any

from config_fila import get_config_fila, save_config_fila


def obter_configuracao() -> dict[str, Any]:
    return get_config_fila()


def salvar_configuracao(config: dict[str, Any]) -> dict[str, Any]:
    save_config_fila(config)
    return {"ok": True, "message": "Configuração salva."}
