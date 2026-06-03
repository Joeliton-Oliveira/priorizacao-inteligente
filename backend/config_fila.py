# -*- coding: utf-8 -*-
"""
Configuração da fila de priorização (calibragem).
Consumida pela API e pela interface atual em Next.js.
Carrega de config_fila.json se existir; senão usa os padrões abaixo.
"""
import json
import copy
from pathlib import Path
from typing import Any

CONFIG_FILA_JSON = Path(__file__).resolve().parent / "config_fila.json"

CONFIG_FILA: dict[str, Any] = {
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
    "incremento_por_faixa_bug": {"CRITICA": 0.2, "ALTA": 0.4, "MEDIA": 0.8, "BAIXA": 1.2},
    "incremento_por_faixa_incremento": {
        "quick_wins": 0.5,
        "grandes_projetos": 0.4,
        "preenchimento": 1.0,
        "desperdicio": 0.7,
    },
    # Limites WIP do Kanban consumidos pela API e pelo frontend atual.
    "wip": {"TO_DO": 5, "DEVELOP": 2, "TEST": 2, "DEPLOY": 1},
}


def _merge_deep(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _merge_deep(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def get_config_fila() -> dict[str, Any]:
    """Retorna a configuração da fila. Carrega de config_fila.json se existir."""
    if CONFIG_FILA_JSON.exists():
        try:
            with open(CONFIG_FILA_JSON, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            merged = _merge_deep(CONFIG_FILA, loaded)
            merged["vazao"] = _normalizar_vazao(merged.get("vazao"))
            return merged
        except Exception:
            pass
    out = copy.deepcopy(CONFIG_FILA)
    out["vazao"] = _normalizar_vazao(out.get("vazao"))
    return out


def _normalizar_vazao(vazao: dict[str, Any] | None) -> dict[str, int]:
    """Garante percentuais de bugs entre 0 e 100; melhorias completam 100%."""
    if not vazao:
        return {"bugs": 60, "incrementos": 40}
    try:
        bugs = int(round(float(vazao.get("bugs", 60))))
    except (TypeError, ValueError):
        bugs = 60
    bugs = max(0, min(100, bugs))
    return {"bugs": bugs, "incrementos": 100 - bugs}


def save_config_fila(config: dict[str, Any]) -> None:
    """Salva a configuração em config_fila.json."""
    merged = _merge_deep(CONFIG_FILA, config)
    merged["vazao"] = _normalizar_vazao(merged.get("vazao"))
    with open(CONFIG_FILA_JSON, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
